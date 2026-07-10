# Testing Strategy

## Mục tiêu

Đảm bảo hệ thống RAG không chỉ chạy được mà còn có thể kiểm tra, tái lập và chặn regression. Testing gồm test code truyền thống và eval test đặc thù LLMOps.

## Các lớp test

| Lớp | Mục tiêu | Khi chạy |
|---|---|---|
| Unit test | Kiểm tra hàm/module nhỏ | Mỗi commit |
| Integration test | Kiểm tra service kết nối nhau | PR/CI |
| E2E test | Kiểm tra luồng ingest -> QA | Milestone |
| Evaluation test | Đánh giá chất lượng RAG | CI/nightly |
| Guardrail test | Kiểm tra security/refusal | PR/nightly |
| Load smoke test | Kiểm tra latency/cost cơ bản | Milestone |

## Unit tests cần có

- text cleaner;
- Vietnamese normalizer;
- chunker;
- metadata extractor;
- retrieval metric calculator;
- prompt renderer;
- citation parser;
- quality gate decision;
- cost calculator;
- feedback classifier.

## Integration tests cần có

- API kết nối Postgres.
- API kết nối Qdrant.
- API gọi LiteLLM mock.
- Ingest tạo chunks và index.
- QA flow trả answer với trace.
- Prompt registry tích hợp runtime.
- Evaluation đọc golden set và trace.

## E2E scenario

1. Ingest một tài liệu nhỏ.
2. Tạo index.
3. Tạo prompt active.
4. Gửi câu hỏi có đáp án.
5. Nhận answer có citation.
6. Gửi câu hỏi không có đáp án.
7. Nhận refusal.
8. Gửi feedback negative.
9. Feedback xuất hiện trong queue.

## Evaluation tests

- Smoke set 50 câu trong CI.
- Full set 300 câu nightly.
- Adversarial set 20 câu khi thay guardrail/prompt.
- Regression tests cho 16 thay đổi giả lập.

## Acceptance criteria

- Unit tests pass.
- Integration tests pass.
- E2E smoke pass.
- Quality gate PASS cho baseline.
- Gate BLOCK được thay đổi xấu giả lập.
- Test report lưu artifact.

## Rủi ro

| Rủi ro | Cách xử lý |
|---|---|
| Test LLM không ổn định | Mock provider cho unit/integration; eval riêng |
| CI tốn tiền | Smoke set nhỏ, cache, model rẻ |
| Test quá chậm | Chia smoke/full/nightly |
| Snapshot answer dễ vỡ | Đánh giá bằng metric/rubric thay vì exact string |

