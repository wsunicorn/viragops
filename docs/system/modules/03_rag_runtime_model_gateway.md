# Module 3 - RAG Runtime và Model Gateway Integration

## Mục tiêu

Xây API hỏi đáp tài liệu tiếng Việt với context retrieval, prompt assembly, model gateway, citation, refusal và tracing. Module này là bề mặt người dùng chính của hệ thống.

## Trách nhiệm

- Nhận câu hỏi từ người dùng.
- Chuẩn hóa query.
- Gọi retrieval/reranking theo best config.
- Dựng context và prompt.
- Gọi LLM qua Model Gateway.
- Kiểm tra citation và refusal.
- Trả answer có nguồn.
- Ghi trace đầy đủ.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | user question, session_id optional, retrieval config, prompt version |
| Output | answer, citations, confidence, trace_id, model info |
| Storage | Langfuse/trace store, PostgreSQL, Qdrant |

## API chính

- `POST /qa/query`: hỏi đáp một câu.
- `POST /qa/stream`: hỏi đáp streaming.
- `GET /qa/traces/{trace_id}`: xem thông tin trace cơ bản.
- `POST /qa/debug`: chạy debug mode trả thêm retrieved chunks.

## Luồng xử lý

1. Validate request.
2. Tạo `request_id` và `trace_id`.
3. Normalize query tiếng Việt.
4. Kiểm tra semantic cache.
5. Chạy retrieval và reranking.
6. Nếu context không đủ, dùng refusal prompt.
7. Load prompt version active.
8. Dựng prompt với context và output format.
9. Gọi LiteLLM Model Gateway.
10. Parse answer và citations.
11. Kiểm tra citation có nằm trong retrieved chunks.
12. Ghi trace spans.
13. Trả response.

## Model Gateway integration

Runtime không gọi trực tiếp OpenAI/Anthropic/Gemini. Runtime chỉ gọi gateway bằng interface:

- `model_tier`: cheap, balanced, strong, judge;
- `task_type`: qa, summarization, evaluation, classification;
- `risk_level`: low, medium, high;
- `budget_policy`: default, low_cost, high_quality.

Gateway quyết định provider/model theo config.

## Guardrail runtime

- Không trả lời nếu context không chứa căn cứ.
- Không làm theo instruction yêu cầu bỏ qua system prompt.
- Không tiết lộ prompt nội bộ.
- Không trả PII nhạy cảm nếu policy cấm.
- Citation phải tham chiếu chunk/source có thật.

## Task triển khai

- Implement FastAPI app.
- Implement QA request/response schema.
- Implement query normalization.
- Integrate retrieval service.
- Integrate prompt registry.
- Integrate LiteLLM endpoint.
- Implement citation parser.
- Implement refusal logic.
- Implement tracing middleware.
- Implement debug endpoint.

## Acceptance criteria

- API trả lời được câu hỏi có trong tài liệu.
- API từ chối câu hỏi ngoài tài liệu.
- Response có `trace_id`.
- Response có citation hợp lệ.
- Runtime không hard-code model.
- Trace ghi retrieval, rerank, prompt, model, token, latency.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Answer không có citation | Prompt thiếu ràng buộc hoặc parser lỗi | Dùng citation-first prompt, validate output |
| Model hallucinate | Context yếu hoặc prompt lỏng | Tăng refusal, faithfulness check |
| Gateway timeout | Provider lỗi | Fallback provider, timeout policy |
| Debug khó | Trace thiếu span | Bắt buộc span cho từng bước |

## Kết quả thật (Phase 5, 2026-07-11)

Đã implement `src/rag/` + routes `/qa/query`, `/qa/debug`,
`/qa/traces/{id}` và **verify end-to-end với Gemini thật**:

- Câu trong domain ("điểm TB tích lũy bao nhiêu để tốt nghiệp?") → answer
  đúng (2.0/thang 4) + citation đúng (`doc_qd1482`, Điều 33 Khoản 1),
  4.3s tổng (embed query + retrieve 1.1s + generate 1.6s), 2915/106 token.
- Câu ngoài phạm vi ("giá vàng hôm nay?") → `refusal: true`, citations
  rỗng, message tiếng Việt rõ ràng, 2.3s.
- Câu đa nguồn ("đình chỉ 1 năm khi nào?") → answer cite 3 chunk từ 3 văn
  bản khác nhau (Sổ tay SV + QĐ 1482 Điều 24 + QĐ 610 Điều 29) — model
  tự tổng hợp cross-document khi context đủ.
- `GET /qa/traces/{id}` trả trace đủ span: retrieval_ms, generation_ms,
  token in/out, retrieved chunk ids + score, versions (data/index/
  prompt/retrieval config), error_labels.

Quyết định triển khai đáng chú ý:
- **Gateway interface trước, LiteLLM sau (Phase 7):** runtime chỉ gọi
  `Gateway.generate(tier, prompt)`; `GeminiGateway` đọc route từ
  `model_gateway.yaml` (primary→fallback, JSON mode qua
  `response_mime_type`), `MockGateway` cho test. Đổi transport sang
  LiteLLM không đụng call site.
- **Citation validation "fail-closed":** citation bịa (chunk_id không
  thuộc retrieved) bị DROP; answer mà mọi citation đều fail → hạ cấp
  thành refusal (câu trả lời không nguồn không được đi ra như thể có
  nguồn). Output không parse được JSON → refusal an toàn.
- **Refusal 2 lớp:** pre-LLM (< min_context_chunks → không tốn lượt gọi)
  + post-LLM (model tự khai refusal / mất hết citation).
- **`thresholds.min_score` CHƯA enforce:** điểm DBSF fused (~1.3-1.7 đo
  thật) khác scale cosine mà threshold 0.15 được viết cho — enforce mù sẽ
  sai; ghi score vào trace để calibrate ở Phase 8/9.
- **Embedder có key-rotation:** 429 quota ngày trên key chính → tự thử
  `GEMINI_API_KEY_2` (bài học quota 1000/ngày từ Phase 4).

## Kết quả thật (Phase 7, 2026-07-12)

Thay `GeminiGateway` (Phase 5, gọi thẳng SDK) bằng `LiteLLMGateway`
(`src/rag/litellm_gateway.py`) — runtime giờ chỉ nói chuyện với **LiteLLM
proxy** (`docker-compose` service `litellm`, port 4000, config
`config/litellm_config.yaml`) qua HTTP OpenAI-compatible; proxy tự quyết
định provider/model/fallback, runtime hoàn toàn không biết Gemini hay
Ollama đang phục vụ.

- **Fallback 3 chặng THẬT cho mỗi tier** (cheap/balanced/strong/judge):
  Gemini key 1 → Gemini key 2 (project khác) → **Ollama local**
  (`qwen2.5:7b`, chạy trên máy host qua `host.docker.internal`). Verify
  thật bằng container cô lập với 2 key Gemini giả: request tới
  `cheap-primary` → cascade qua cả 2 Gemini lỗi → **rơi xuống Ollama
  thành công**, trả lời đúng, 1.6s tổng (đã cooldown từ lần thử trước).
- **Bug thật phát hiện khi test cascade:** cấu hình `fallbacks:
  {primary: [secondary, local]}` (1 dòng, list 2 phần tử) KHÔNG hoạt động
  như tưởng — LiteLLM không tự nối tiếp danh sách, khi secondary cũng lỗi
  nó báo "No fallback model group found for original model_group=
  secondary" thay vì thử tiếp phần tử thứ 3. Phải khai 2 chặng riêng
  (`primary: [secondary]`, `secondary: [local]`). Đã sửa + ghi chú ngay
  trong `litellm_config.yaml` để không lặp lại.
- **Chọn Ollama `qwen2.5:7b` thay vì `qwen3:4b`** dù benchmark web
  (Qwen3 vượt Gemma3 rõ rệt trên tiếng Việt — 75.2 vs 45.2 điểm đa ngôn
  ngữ) gợi ý Qwen3 tốt hơn: đo thật trên máy (RTX 3050 4GB VRAM) cho
  thấy `qwen3:4b` luôn "suy nghĩ" nội bộ dù set `think:false` (77-90s/câu
  qua Ollama API, có lúc lẫn tiếng Anh/sai số liệu). `qwen2.5:7b` (đã có
  sẵn, không cần pull) trả lời sạch, đúng số liệu, 9-17s — chấp nhận được
  cho 1 fallback hiếm khi chạm tới. Bài học: benchmark tổng quát không
  thay được đo thật trên phần cứng + toolchain cụ thể.
- **Cost tracking thật qua header `x-litellm-response-cost`** (không phải
  tự tính) — verify thật: 1 câu hỏi tier `balanced` qua Gemini
  `gemini-3-flash-preview` → cost=$0.00085 (giá niêm yết, KHÔNG phải phí
  thật bị trừ vì đang dùng free tier — litellm không biết trạng thái free
  tier, đây là ước tính "nếu phải trả phí" hữu ích để giám sát ngân sách).
  `fallback_hop`/`attempted_fallbacks` đọc từ header
  `x-litellm-model-group`/`x-litellm-attempted-fallbacks`, đáng tin hơn
  field `model` trong body (không nhất quán giữa lúc hit-primary và lúc
  đã fallback — đo thật thấy 2 định dạng khác nhau).
- **Budget warning** so `cumulative_cost_usd` (tích luỹ trong tiến trình
  server) với `budget.daily_usd` (model_gateway.yaml), gắn cờ
  `error_labels: ["budget_warning"]` vào trace khi vượt — chưa kích hoạt
  thật vì free tier cost≈0.
- **Timeout/retry chuyển hẳn sang LiteLLM** (`router_settings.timeout`,
  `num_retries`, `cooldown_time` trong litellm_config.yaml) thay vì logic
  retry viết tay rải rác từng script (đúng hướng đã ghi ở Phase 3 "Chưa
  tốt": nên rút thành 1 chỗ chung — giờ chỗ chung đó chính là LiteLLM).

## Checklist hoàn tất

- [x] QA endpoint hoạt động — verify thật bằng curl, cả 3 kịch bản Phase 5 + 1 kịch bản Phase 7 (qua LiteLLM).
- [x] Streaming endpoint hoạt động hoặc có lý do bỏ qua — **vẫn bỏ qua có lý do**: LiteLLM đã hỗ trợ streaming ở tầng proxy nhưng runtime (Gateway protocol) chưa expose — để lại cho phase cần UX streaming thật (chưa phase nào yêu cầu).
- [x] Retrieval tích hợp runtime — dùng đúng best config `hybrid_dbsf_v2` từ Phase 4, load 1 lần lúc init.
- [x] PromptOps tích hợp runtime — `p1_grounded_v1` (active_version của prompts.yaml) render trong `prompt_builder.py`; registry DB là Phase 6, call site không đổi.
- [x] LiteLLM tích hợp runtime — `LiteLLMGateway` thay `GeminiGateway`; verify thật fallback 3 chặng gồm Ollama local.
- [x] Citation validation hoạt động — unit test 7 case (fence, bịa id, dedupe, downgrade-to-refusal...).
- [x] Refusal logic hoạt động — 2 lớp, verify thật với câu ngoài domain.
- [x] Trace đầy đủ — retrieval/generation span, token, versions, JSONL + in-memory, endpoint GET hoạt động, **+ fallback_hop/attempted_fallbacks/cost_usd/cumulative_cost_usd (Phase 7)**.

