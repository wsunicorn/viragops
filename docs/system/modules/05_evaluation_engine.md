# Module 5 - Evaluation Engine

## Mục tiêu

Xây engine đánh giá RAG 4 tầng: retrieval, context, generation và operations. Evaluation Engine cung cấp số liệu cho experiment, quality gate, dashboard và báo cáo khóa luận.

## 4 tầng đánh giá

| Tầng | Metric |
|---|---|
| Retrieval | Recall@k, MRR, nDCG, Hit Rate |
| Context | Context Precision, Context Recall, Context Relevance |
| Generation | Faithfulness, Answer Relevance, Citation Accuracy, Refusal Accuracy, Hallucination Rate |
| Operations | Latency, cost/request, token usage, error rate, cache hit rate |

## Input và output

| Loại | Nội dung |
|---|---|
| Input | golden set, traces, answers, retrieved chunks, configs |
| Output | eval result, metric scores, failure cases, report |
| Storage | PostgreSQL, MLflow, Langfuse, CSV/Markdown |

## Evaluation modes

- `smoke`: 50 câu, chạy trong CI.
- `full`: 300 câu, chạy nightly hoặc trước milestone.
- `targeted`: subset theo category, dùng debug lỗi.
- `judge_sample`: dùng model judge cho một phần hoặc toàn bộ câu hỏi.
- `human_review`: reviewer kiểm tra mẫu lỗi.

## Luồng xử lý

1. Load eval config.
2. Load golden set subset.
3. Chạy hệ thống hoặc đọc trace có sẵn.
4. Tính retrieval metrics.
5. Tính context metrics.
6. Tính generation metrics bằng RAGAS/DeepEval/custom.
7. Tính operations metrics.
8. Gắn error labels cho case fail.
9. Xuất eval report.
10. Gửi result cho Quality Gate.

## Task triển khai

- Implement golden set loader.
- Implement retrieval metric calculator.
- Implement context metric calculator.
- Integrate RAGAS/DeepEval.
- Implement custom citation/refusal metrics.
- Implement LLM-as-a-Judge wrapper qua Model Gateway.
- Implement eval report writer.
- Implement failure case export.

## Acceptance criteria

- Chạy được smoke eval 50 câu.
- Chạy được full eval 300 câu.
- Có metric theo từng câu và tổng hợp.
- Có failure case list.
- Có eval result ID để quality gate sử dụng.
- Có human review sampling output.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Judge không nhất quán | LLM-as-a-Judge biến động | Dùng rubric rõ, temperature thấp, human sample |
| Metric không phù hợp tiếng Việt | Tool metric thiên tiếng Anh | Thêm custom metric và manual review |
| Eval quá tốn tiền | Judge mọi câu quá nhiều lần | Smoke set, sampling, cache judge result |
| Result khó phân tích | Chỉ có score tổng | Xuất failure cases và labels |

## Checklist hoàn tất

- [ ] Golden set loader hoạt động.
- [ ] Retrieval metrics hoạt động.
- [ ] Context metrics hoạt động.
- [ ] Generation metrics hoạt động.
- [ ] Operations metrics hoạt động.
- [ ] LLM judge hoạt động.
- [ ] Eval report xuất được.
- [ ] Failure cases xuất được.

