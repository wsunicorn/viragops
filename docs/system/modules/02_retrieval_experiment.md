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

## Kết quả thật (Phase 4, 2026-07-11)

- **Relevance ground truth:** `src/retrieval/citation_matcher.py` khớp
  expected_citations → chunk_ids cho 71/71 câu không-refusal (42
  structural qua parse Điều/Khoản + range, 30 lexical fallback cho tài
  liệu không có heading Điều). Metric dạng citation-coverage (1 citation
  = 1 nhóm chunk chấp nhận được) — xem docstring `src/retrieval/metrics.py`.
- **Experiment 2 (8 config, `results_retrieval_reranking.md`):** hybrid
  DBSF prefetch-40 thắng — recall@5=0.993, hit=1.000, MRR=0.827,
  nDCG@5=0.869, p95=17ms. Thứ tự: DBSF > RRF (0.979) > sparse BM25 tự
  viết (0.944) > dense thuần (0.908). Đã chốt vào `config/retrieval.yaml`
  (`hybrid_dbsf_v2`).
- **Reranker:** bge-reranker-v2-m3 KHÔNG tải được (ISP chặn CDN
  huggingface.co, cùng lỗi fastembed Phase 3) → thay bằng Gemini listwise
  (`src/retrieval/reranker.py`). Kết quả thật: rerank giúp dense-only
  (0.908→0.923) nhưng LÀM GIẢM hybrid (0.979→0.958, MRR 0.819→0.718) và
  cộng ~1s/câu → tắt reranker trong config chính thức. Jina/ViRanker
  trong kế hoạch gốc chưa thử (cùng rào cản tải model).
- **Experiment 1 (chunking ablation, `results_chunking_ablation.md`):**
  structure_aware thắng — recall@5=0.979 ngang recursive nhưng MRR 0.812
  vs 0.690 (xếp hạng tốt hơn hẳn); parent_child thấp nhất (0.923) vì
  parent+child trùng nội dung chen top-5. Xác nhận bằng số liệu lựa chọn
  default strategy của Phase 3. So kế hoạch gốc 8 config: fixed
  256/512/768 gộp còn 1 mức (300 token), semantic/table-aware chưa
  implement — ghi nhận là thiếu so kế hoạch, không phải đã thử và loại.
- **Lưu ý so sánh chéo strategy:** mỗi strategy được chấm trên relevant
  set TỰ SINH từ citation matcher trên chunk của chính nó (fair theo
  granularity), trong đó fixed/recursive không có section → 100% lexical
  matching — so sánh giữa strategy vì vậy có độ nhiễu nhất định.

## Kết quả thật (tái xác nhận trên golden set 300 câu, 2026-07-12)

Sau khi mở rộng golden set 76→300 câu (xem `golden_set_review.md` mục
"Batch 4"), chạy lại nguyên vẹn cả 2 experiment trên `data_20260712` /
249 câu có căn cứ (thay vì 71):

- **Kết luận KHÔNG đổi:** `hybrid_dbsf_pre40` vẫn thắng (recall@5=0.932,
  giảm từ 0.993 — kỳ vọng khi bộ câu lớn/đa dạng hơn, không phải retrieval
  kém đi), và `structure_aware` vẫn thắng chunking ablation (recall@5=
  0.906). Thứ hạng tương đối giữa các config giữ nguyên: DBSF > RRF >
  {sparse, dense} cho experiment 2; structure_aware > {fixed, parent_child}
  > recursive cho experiment 1.
- **Phát hiện mới, khác kết luận cũ:** trên 249 câu, Gemini rerank thực ra
  **giúp** cả dense (0.882→0.894) và hybrid_rrf (0.906→0.928) — kết luận
  cũ "rerank luôn làm giảm chất lượng hybrid" chỉ đúng khi so với DBSF,
  không đúng khi so với RRF thuần. Rerank vẫn không vượt được hybrid_dbsf
  không-rerank, và p95 latency đo được **61 giây/câu** khi chạy 250 câu
  liên tục và bị Gemini rate-limit thật (retry backoff 10-30s lặp lại) —
  đây là bằng chứng thực nghiệm mạnh hơn cho việc không bật reranker
  (không đáng đổi latency), thay vì lý do "chất lượng luôn tệ hơn" như
  ghi nhận ban đầu trên mẫu nhỏ.
- **Quota vận hành:** re-run tốn ~1800 embedding item (1339 chunk 3
  strategy còn thiếu + 250 query), vượt xa 1 key/ngày (1000) — cần thêm 2
  key nữa (tổng 4) mới chạy xong trong 1 phiên. Xem CHECKLIST Phase 4
  "Chưa tốt" để biết chi tiết.
- Không đổi `config/retrieval.yaml` — số liệu mới CHỐT LẠI cùng lựa chọn
  cũ, không phải đổi hướng.

## Checklist hoàn tất

- [x] Có retrieval config schema (`config/experiments_retrieval.yaml` + RetrievalConfig dataclass).
- [x] Dense retrieval chạy được (`src/retrieval/retriever.py`).
- [x] Sparse/BM25 baseline chạy được (BM25 tự viết, cũng là vector sparse trong Qdrant).
- [x] Hybrid retrieval chạy được (RRF + DBSF server-side qua Query API).
- [x] Reranker chạy được *(Gemini listwise — cross-encoder bge chưa tải được, xem ghi chú trên)*.
- [x] Metric retrieval tính đúng (unit test 51 case, gồm nhóm-coverage, no-double-credit nDCG).
- [x] Chạy đủ experiment nhóm retrieval (8 config + 4 strategy ablation, chạy thật trên Qdrant).
- [x] Có best retrieval config (`hybrid_dbsf_v2` trong `config/retrieval.yaml`).
- [x] Có report phân tích lỗi (mục failure trong 2 file results_*.md — best config 0 câu trượt; ablation 1 câu q_024).

