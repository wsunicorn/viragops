# Kết quả experiment: chunking_ablation

> Sinh bởi `scripts/run_experiment.py` lúc 20260711_0842 UTC. data_version=`data_20260711`, index_version=`idx_20260711_geminiembedding001`, embedding=`gemini-embedding-001`. Metric tính ở k=5 theo `contracts/metric_definitions.md`; relevance = citation-coverage (xem docstring `src/retrieval/metrics.py`). Latency chỉ tính retrieval(+rerank), KHÔNG gồm embed query (đã cache) — p95 API thật ở Phase 5 sẽ cao hơn.

| config | mode | rerank | recall@5 | hit rate | MRR | nDCG@5 | p50 ms | p95 ms |
|---|---|---|---:|---:|---:|---:|---:|---:|
| hybrid_rrf_recursive | hybrid_rrf | none | 0.979 | 0.986 | 0.690 | 0.761 | 5.3 | 19.7 |
| hybrid_rrf_structure_aware **(best)** | hybrid_rrf | none | 0.979 | 0.986 | 0.812 | 0.853 | 5.4 | 19.4 |
| hybrid_rrf_fixed | hybrid_rrf | none | 0.965 | 0.972 | 0.699 | 0.764 | 6.6 | 23.9 |
| hybrid_rrf_parent_child | hybrid_rrf | none | 0.923 | 0.930 | 0.795 | 0.824 | 5.6 | 19.2 |

- Best config: **hybrid_rrf_structure_aware** — recall@5=0.979, nDCG@5=0.853 (ĐẠT target recall >= 0.85 của metric_definitions.md).
- Số câu đánh giá: 71 (câu không-refusal có citation khớp được).

## Phân tích lỗi — câu hit@5=0 với best config (1 câu)

| question | hỏi | citation kỳ vọng | top-1 nhận được |
|---|---|---|---|
| q_024 | Sinh viên hệ vừa làm vừa học, đại học liên thông khóa tuyển sinh từ 20 | Điều kiện xét tốt nghiệp, mục 1.e | doc_qd1482_quy_che_tin_chi · Điều 33, Khoản 1 |