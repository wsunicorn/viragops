# Module 6 - CI/CD Quality Gate

## Mục tiêu

Chặn các thay đổi làm giảm chất lượng RAG trước khi deploy. Quality Gate biến evaluation thành quyết định vận hành: PASS, WARN hoặc BLOCK.

## Thay đổi phải qua gate

- Prompt mới.
- Model gateway config mới.
- Retrieval config mới.
- Chunking/data/index mới.
- Code runtime thay đổi.
- Guardrail policy thay đổi.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | eval result, baseline metrics, threshold config |
| Output | gate decision, regression report, deploy/block status |
| Storage | GitHub Actions artifact, PostgreSQL, Markdown report |

## Decision policy

- `PASS`: tất cả critical metric đạt, warning metric không giảm nghiêm trọng.
- `WARN`: critical đạt nhưng warning metric vi phạm.
- `BLOCK`: bất kỳ critical metric vi phạm hoặc regression vượt ngưỡng.

Critical metric mặc định:

- Retrieval Recall@5;
- Faithfulness;
- Answer Relevance;
- Hallucination Rate;
- Refusal Accuracy;
- p95 latency;
- error rate.

## Luồng CI

1. PR hoặc config change được tạo.
2. CI phát hiện loại thay đổi.
3. Chạy smoke eval 50 câu.
4. Tính metric.
5. So sánh baseline.
6. Gate quyết định PASS/WARN/BLOCK.
7. Nếu PASS, cho merge/deploy.
8. Nếu WARN, yêu cầu reviewer xác nhận.
9. Nếu BLOCK, giữ version cũ.
10. Nightly job chạy full eval 300 câu.

## Task triển khai

- Tạo `quality_gate.yaml`.
- Implement gate evaluator.
- Implement baseline comparison.
- Implement GitHub Actions workflow.
- Implement Markdown gate report.
- Implement failure case attachment.
- Implement rollback/version keep policy.

## Acceptance criteria

- Gate chạy được từ command line.
- Gate chạy được trong GitHub Actions.
- Gate tạo report rõ PASS/WARN/BLOCK.
- Gate chặn được ít nhất 8 thay đổi xấu giả lập.
- Gate cho pass các thay đổi tốt/trung tính.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Gate quá chặt | Threshold không có margin | Dùng regression margin 2-3% |
| Gate quá lỏng | Chỉ đo answer relevance | Thêm faithfulness/citation/refusal |
| CI quá chậm | Chạy full eval mọi PR | Smoke set 50 câu trong CI, full eval nightly |
| Report khó đọc | Chỉ log console | Xuất Markdown report |

## Checklist hoàn tất

- [ ] Có quality gate config.
- [ ] Gate CLI hoạt động.
- [ ] GitHub Actions workflow có smoke eval.
- [ ] Gate report có metric và decision.
- [ ] Baseline comparison hoạt động.
- [ ] Có test thay đổi tốt/xấu giả lập.
- [ ] BLOCK giữ version cũ.

