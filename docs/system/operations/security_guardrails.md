# Security và Guardrails

## Mục tiêu

Giảm rủi ro prompt injection, data leakage, PII exposure, hallucination nguy hiểm và unbounded cost. Security trong project này tập trung vào LLM/RAG safety ở mức khóa luận production-like.

## Threat model

| Rủi ro | Ví dụ | Hành động |
|---|---|---|
| Prompt injection | "Bỏ qua hướng dẫn trước đó..." | System prompt cứng, adversarial eval |
| Data leakage | Lộ prompt nội bộ/API key | Không log secret, không trả prompt |
| PII leakage | Log thông tin cá nhân | Mask PII trong log |
| Hallucination | Trả lời ngoài tài liệu | Refusal policy, faithfulness check |
| Context poisoning | Tài liệu chứa instruction độc hại | Tách document text khỏi system instruction |
| Excessive cost | User spam câu hỏi dài | Rate limit, budget manager |
| Provider abuse | Gọi model mạnh cho mọi request | Routing policy và quota |

## Guardrail policy

Hệ thống phải từ chối hoặc cảnh báo khi:

- câu hỏi yêu cầu bỏ qua system instruction;
- câu hỏi yêu cầu tiết lộ prompt, API key, config nội bộ;
- câu hỏi ngoài domain và không có căn cứ;
- context không đủ để trả lời;
- answer không có citation hợp lệ;
- request vượt rate limit hoặc budget;
- input chứa PII nhạy cảm và policy yêu cầu mask.

## Prompt rules

- Luôn nhắc model chỉ dùng context.
- Luôn yêu cầu trích dẫn nguồn.
- Nếu không có căn cứ, trả lời "không tìm thấy thông tin trong tài liệu".
- Không cho model tự bịa điều/khoản.
- Không đưa raw retrieved context vào answer nếu chứa dữ liệu nhạy cảm.

## Test adversarial

Tối thiểu 20 câu adversarial:

- yêu cầu bỏ qua prompt;
- yêu cầu in system prompt;
- yêu cầu trả lời ngoài tài liệu;
- yêu cầu tạo thông tin giả;
- câu hỏi thiếu dấu hoặc cố tình mập mờ;
- câu hỏi chèn instruction vào dạng trích dẫn;
- câu hỏi yêu cầu truy cập dữ liệu không có quyền.

## Logging policy

- Mask API keys, tokens, passwords.
- Mask PII nếu phát hiện.
- Không log full prompt trong public log.
- Trace debug chỉ cho admin/dev.
- Feedback comment có thể chứa dữ liệu nhạy cảm, cần sanitize trước report.

## Acceptance criteria

- Adversarial set chạy qua quality gate.
- Prompt injection không làm hệ thống bỏ qua system instruction.
- Câu hỏi ngoài tài liệu được refusal đúng.
- Không có secret trong log hoặc report.
- Citation validation chặn answer không có nguồn.

