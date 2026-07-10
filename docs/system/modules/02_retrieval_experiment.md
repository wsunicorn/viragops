# Module 2 - Retrieval Experiment Layer

## Mục tiêu

Xây lớp thực nghiệm retrieval để so sánh chunking, retrieval strategy, fusion, reranking và top-k. Module này giúp chọn cấu hình retrieval tốt nhất bằng số liệu, không chọn cảm tính.

## Trách nhiệm

- Chạy retrieval trên golden set.
- So sánh dense, sparse/BM25, hybrid RRF/DBSF.
- So sánh reranker.
- Đo Recall@k, MRR, nDCG, context precision/recall.
- Lưu experiment config và result.
- Xuất best retrieval config cho RAG runtime.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | chunks/index, golden set, retrieval configs |
| Output | retrieval metrics, best config, experiment report |
| Storage | MLflow, DVC, PostgreSQL, CSV/Markdown report |

## Component nội bộ

- `retriever_dense`: vector search.
- `retriever_sparse`: BM25 hoặc sparse vector search.
- `hybrid_fusion`: RRF/DBSF.
- `reranker`: bge/Jina/ViRanker.
- `experiment_runner`: chạy batch config.
- `metrics_calculator`: tính retrieval metrics.
- `report_writer`: xuất bảng kết quả.

## Config cần hỗ trợ

- chunking strategy;
- embedding model;
- retrieval type: dense, sparse, hybrid;
- fusion method: RRF, DBSF;
- top-k before rerank;
- top-k after rerank;
- reranker model;
- score threshold;
- query normalization on/off.

## Luồng xử lý

1. Load golden set và relevant chunks.
2. Load danh sách retrieval configs.
3. Với mỗi config, chạy retrieval cho từng câu hỏi.
4. Lưu candidate chunks và score.
5. Nếu có reranker, rerank candidates.
6. Tính metric theo từng câu và tổng hợp.
7. Ghi experiment result vào MLflow/DVC.
8. Xuất bảng so sánh và chọn best config.

## Task triển khai

- Implement interface chung `retrieve(query, config)`.
- Implement dense retrieval bằng Qdrant.
- Implement sparse retrieval hoặc BM25 baseline.
- Implement hybrid fusion.
- Implement reranker wrapper.
- Implement metric Recall@k, MRR, nDCG.
- Implement result export CSV/Markdown.
- Implement experiment comparison dashboard hoặc notebook.

## Acceptance criteria

- Chạy được ít nhất 8 config retrieval/reranking.
- Kết quả có Recall@5, MRR, nDCG, latency.
- Mỗi result gắn `data_version`, `index_version`, `retrieval_config_id`.
- Chọn được best config dựa trên metric và latency.
- Report có phân tích lỗi retrieval failure.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Recall thấp | Chunking sai hoặc embedding yếu | So sánh chunking, thêm hybrid retrieval |
| Latency cao | Rerank quá nhiều candidates | Giảm top-k before rerank, cache |
| Metric sai | relevant chunks không chuẩn | Review golden set và relevant chunk mapping |
| Hybrid không cải thiện | Fusion weight chưa phù hợp | Thử RRF/DBSF và normalize score |

## Checklist hoàn tất

- [ ] Có retrieval config schema.
- [ ] Dense retrieval chạy được.
- [ ] Sparse/BM25 baseline chạy được.
- [ ] Hybrid retrieval chạy được.
- [ ] Reranker chạy được.
- [ ] Metric retrieval tính đúng.
- [ ] Chạy đủ experiment nhóm retrieval.
- [ ] Có best retrieval config.
- [ ] Có report phân tích lỗi.

