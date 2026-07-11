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

## Checklist hoàn tất

- [x] QA endpoint hoạt động — verify thật bằng curl, cả 3 kịch bản trên.
- [x] Streaming endpoint hoạt động hoặc có lý do bỏ qua — **bỏ qua có lý do**: gateway hiện là REST đơn giản, streaming để Phase 7 (LiteLLM có sẵn streaming) — tránh viết 2 lần.
- [x] Retrieval tích hợp runtime — dùng đúng best config `hybrid_dbsf_v2` từ Phase 4, load 1 lần lúc init.
- [x] PromptOps tích hợp runtime — `p1_grounded_v1` (active_version của prompts.yaml) render trong `prompt_builder.py`; registry DB là Phase 6, call site không đổi.
- [ ] LiteLLM tích hợp runtime — **Phase 7 theo kế hoạch** (gateway interface đã tách sẵn chỗ cắm).
- [x] Citation validation hoạt động — unit test 7 case (fence, bịa id, dedupe, downgrade-to-refusal...).
- [x] Refusal logic hoạt động — 2 lớp, verify thật với câu ngoài domain.
- [x] Trace đầy đủ — retrieval/generation span, token, versions, JSONL + in-memory, endpoint GET hoạt động.

