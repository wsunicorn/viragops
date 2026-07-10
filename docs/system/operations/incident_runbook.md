# Incident Runbook

## Mục tiêu

Hướng dẫn xử lý các sự cố thường gặp trong hệ thống LLMOps/RAGOps.

## Incident 1 - Hallucination tăng

Triệu chứng:

- hallucination rate > 5%;
- user feedback negative tăng;
- faithfulness giảm.

Xử lý:

1. Lấy các trace bị label hallucination.
2. Kiểm context có đúng không.
3. Nếu context sai, chuyển sang incident retrieval failure.
4. Nếu context đúng, kiểm prompt version/model route.
5. Rollback prompt nếu vừa thay đổi.
6. Tăng refusal/citation constraint.
7. Chạy targeted eval.
8. Chỉ deploy lại nếu quality gate PASS.

## Incident 2 - Retrieval failure

Triệu chứng:

- Recall@5 giảm;
- retrieval hit rate thấp;
- answer thiếu căn cứ.

Xử lý:

1. Kiểm data_version và index_version.
2. Kiểm tài liệu nguồn có bị thiếu không.
3. Kiểm chunking strategy.
4. Kiểm embedding/index job gần nhất.
5. Chạy retrieval debug set.
6. Thử hybrid/reranker config.
7. Reindex nếu index stale.
8. Chạy full retrieval experiment nếu thay config lớn.

## Incident 3 - Citation error

Triệu chứng:

- answer có vẻ đúng nhưng citation sai;
- citation_accuracy giảm.

Xử lý:

1. Kiểm metadata chunk.
2. Kiểm parser citation.
3. Kiểm prompt output format.
4. Sửa citation-first prompt nếu cần.
5. Chạy citation targeted eval.

## Incident 4 - Provider outage

Triệu chứng:

- timeout tăng;
- fallback rate tăng;
- API trả lỗi model.

Xử lý:

1. Kiểm LiteLLM logs.
2. Kiểm API key/rate limit.
3. Chuyển route sang fallback provider.
4. Giảm model tier nếu cần.
5. Ghi incident vào report.
6. Chạy smoke eval sau khi đổi route.

## Incident 5 - Cost spike

Triệu chứng:

- cost/request vượt budget;
- input tokens tăng;
- model mạnh bị dùng quá nhiều.

Xử lý:

1. Kiểm prompt version có dài bất thường không.
2. Kiểm top-k/context length.
3. Kiểm routing policy.
4. Bật semantic cache.
5. Bật context compression.
6. Chuyển query đơn giản sang cheap model.
7. Chạy cost-latency-quality eval.

## Incident 6 - Data stale

Triệu chứng:

- người dùng báo thông tin cũ;
- data freshness alert;
- source_version mới hơn index_version.

Xử lý:

1. Xác nhận tài liệu nguồn mới.
2. Chạy ingest/reindex.
3. Chạy smoke eval.
4. Nếu PASS, activate index version mới.
5. Invalidate semantic cache theo data_version.

