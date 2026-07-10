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

## Checklist hoàn tất

- [ ] QA endpoint hoạt động.
- [ ] Streaming endpoint hoạt động hoặc có lý do bỏ qua.
- [ ] Retrieval tích hợp runtime.
- [ ] PromptOps tích hợp runtime.
- [ ] LiteLLM tích hợp runtime.
- [ ] Citation validation hoạt động.
- [ ] Refusal logic hoạt động.
- [ ] Trace đầy đủ.

