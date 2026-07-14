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

## Kết quả thật (Phase 11, 2026-07-14)

- **Feedback KHÔNG giả lập** — `scripts/seed_feedback_from_eval.py` đọc
  `data/eval/eval_full_20260712_0938.csv` (298 câu, `p1_grounded_v1`,
  đường sạch `fallback_hop=primary` — kiểm tra kỹ 2 file full-eval hiện có
  và loại bỏ file kia vì 293/298 câu bị Ollama fallback), join thật sang
  `trace_id` qua `data/traces/traces.jsonl`. Kết quả: 26/26 câu match được
  trace (0 skip) → 2 cluster thật: `citation_error`×`multi_hop`=17,
  `citation_error`×`ambiguous`=9.
- **API verify thật qua server chạy sống**: `POST /qa/query` thật →
  `POST /feedback` với `trace_id` vừa nhận → `GET /feedback/queue` (27→26
  sau `POST /feedback/{id}/review`) → `GET /feedback/clusters` khớp đúng
  26 record + 2 cluster từ seed script.
- **Improvement backlog thật**: `scripts/export_improvement_backlog.py` →
  `results_improvement_backlog_20260714_1354.md`, 2 TICKET, đề xuất sửa
  "prompt" cho cả 2 (đúng mapping `citation_error→prompt`).
- **1 vòng cải tiến ĐẦY ĐỦ, KẾT QUẢ THẬT LÀ TIÊU CỰC** (không phải thành
  công giả định): `p8_citation_multipart_v1` (p7 + bước self-check tường
  minh cho câu nhiều vế) → smoke eval 48/50 câu → so Quality Gate với
  baseline p7 → **BLOCK** (citation_accuracy 0.838→0.775 TỆ HƠN, p95
  latency +63%). Chi tiết + phân tích nguyên nhân:
  `results_prompt_p8_citation_multipart_v1_vs_p7.md`. Không activate —
  đúng chính sách áp dụng nhất quán mọi lần trước (p6/p7 chỉ activate khi
  số liệu thật chứng minh cải thiện).
- Error classifier rule-based (`src/feedback/classifier.py`) đọc thẳng
  field thật đã có sẵn trong trace (`error_labels`/`invalid_citations`/
  `refusal`/`fallback_hop`) — không cần thêm logic phân tích riêng, tái
  dùng đúng dữ liệu Phase 5-10 đã ghi.
- Clustering (`src/feedback/clustering.py`) group theo `(error_label,
  category)` — KHÔNG dùng embedding API (tránh tốn quota Gemini cho một
  tính năng backend/bookkeeping); lexical Jaccard overlap chỉ dùng để
  chọn tối đa 3 câu mẫu/cluster hiển thị cho reviewer.

## Checklist hoàn tất

- [x] Feedback API hoạt động — verify thật qua server sống.
- [x] Feedback linked với trace — `trace_id` bắt buộc, tra qua `RagService.get_trace()`.
- [x] Error taxonomy được dùng nhất quán — 9 nhãn khớp module doc + DB CHECK constraint.
- [x] Error clustering hoạt động — 2 cluster thật, verify qua `GET /feedback/clusters`.
- [x] Human review queue hoạt động — verify thật (27→26 sau review).
- [x] Improvement backlog xuất được — `results_improvement_backlog_20260714_1354.md`.
- [x] Chạy được feedback-improved experiment — p8, kết quả thật (tiêu cực), không activate.

