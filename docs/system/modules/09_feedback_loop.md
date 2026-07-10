# Module 9 - Feedback Loop

## Mục tiêu

Biến feedback người dùng, trace và evaluation failure thành backlog cải tiến có kiểm soát. Feedback Loop không tự sửa production trực tiếp; nó tạo candidate improvement để đi qua evaluation và quality gate.

## Trách nhiệm

- Thu feedback từ người dùng.
- Liên kết feedback với trace_id.
- Phân loại lỗi.
- Gom nhóm lỗi tương tự.
- Tạo human review queue.
- Tạo improvement backlog.
- Đề xuất sửa prompt/data/retrieval/routing.
- Theo dõi improvement velocity.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | user feedback, eval failures, traces, dashboard alerts |
| Output | error clusters, review tasks, improvement tickets |
| Storage | PostgreSQL, issue backlog, report |

## Feedback types

- thumbs up/down;
- comment tự do;
- report wrong answer;
- report missing citation;
- report outdated information;
- report slow response;
- report unsafe answer.

## Error taxonomy

| Label | Ý nghĩa |
|---|---|
| retrieval_failure | Không lấy đúng chunk |
| context_insufficient | Có chunk liên quan nhưng thiếu thông tin |
| hallucination | Answer chứa thông tin ngoài context |
| citation_error | Answer đúng nhưng citation sai/thiếu |
| refusal_error | Từ chối sai hoặc không từ chối khi thiếu căn cứ |
| stale_data | Dữ liệu/index lỗi thời |
| prompt_injection | User cố vượt instruction |
| provider_error | Timeout/rate limit/model degraded |
| cost_latency_issue | Request quá chậm hoặc quá tốn |

## Luồng xử lý

1. Người dùng gửi feedback.
2. Feedback gắn với `trace_id`.
3. Hệ thống lấy trace, answer, context, metrics.
4. Error classifier gán nhãn lỗi.
5. Error clustering gom lỗi tương tự.
6. Human reviewer kiểm tra nhóm ưu tiên.
7. Tạo improvement ticket.
8. Sửa prompt/data/retrieval/routing theo ticket.
9. Chạy evaluation và quality gate.
10. Deploy nếu PASS.
11. Theo dõi lỗi có giảm không.

## Task triển khai

- Implement feedback API.
- Implement feedback schema.
- Link feedback với trace.
- Implement error classifier rule-based.
- Implement clustering theo embedding/error label.
- Implement human review queue.
- Implement improvement backlog export.
- Implement feedback improvement experiment.

## Acceptance criteria

- Feedback lưu được và truy theo trace_id.
- Feedback có error label.
- Có danh sách top error clusters.
- Có human review queue.
- Có ít nhất một vòng cải tiến từ feedback và đo được metric trước/sau.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Feedback không actionable | Chỉ có thumbs down | Bắt comment/category khi negative |
| Không tái hiện được lỗi | Không link trace_id | Feedback bắt buộc gắn trace |
| Cải tiến làm regression | Sửa trực tiếp production | Mọi improvement qua quality gate |
| Quá nhiều lỗi lẻ | Không clustering | Gom theo label + embedding |

## Checklist hoàn tất

- [ ] Feedback API hoạt động.
- [ ] Feedback linked với trace.
- [ ] Error taxonomy được dùng nhất quán.
- [ ] Error clustering hoạt động.
- [ ] Human review queue hoạt động.
- [ ] Improvement backlog xuất được.
- [ ] Chạy được feedback-improved experiment.

