# Kết quả experiment: retrieval_reranking

> Sinh bởi `scripts/run_experiment.py` lúc 20260711_0852 UTC. data_version=`data_20260711`, index_version=`idx_20260711_geminiembedding001`, embedding=`gemini-embedding-001`. Metric tính ở k=5 theo `contracts/metric_definitions.md`; relevance = citation-coverage (xem docstring `src/retrieval/metrics.py`). Latency chỉ tính retrieval(+rerank), KHÔNG gồm embed query (đã cache) — p95 API thật ở Phase 5 sẽ cao hơn.

| config | mode | rerank | recall@5 | hit rate | MRR | nDCG@5 | p50 ms | p95 ms |
|---|---|---|---:|---:|---:|---:|---:|---:|
| hybrid_dbsf_pre20 | hybrid_dbsf | none | 0.993 | 1.000 | 0.824 | 0.866 | 5.6 | 22.4 |
| hybrid_dbsf_pre40 **(best)** | hybrid_dbsf | none | 0.993 | 1.000 | 0.827 | 0.869 | 5.7 | 17.2 |
| hybrid_rrf_pre20 | hybrid_rrf | none | 0.979 | 0.986 | 0.819 | 0.859 | 5.3 | 18.9 |
| hybrid_rrf_pre40 | hybrid_rrf | none | 0.979 | 0.986 | 0.790 | 0.837 | 6.2 | 25.1 |
| hybrid_rrf_rerank_gemini | hybrid_rrf | gemini_listwise | 0.958 | 0.958 | 0.718 | 0.779 | 994.2 | 1110.4 |
| sparse_bm25_top5 | sparse | none | 0.944 | 0.944 | 0.754 | 0.803 | 3.5 | 19.6 |
| dense_rerank_gemini | dense | gemini_listwise | 0.923 | 0.930 | 0.738 | 0.784 | 934.7 | 1104.7 |
| dense_top5 | dense | none | 0.908 | 0.915 | 0.677 | 0.732 | 4.9 | 22.5 |

- Best config: **hybrid_dbsf_pre40** — recall@5=0.993, nDCG@5=0.869 (ĐẠT target recall >= 0.85 của metric_definitions.md).
- Số câu đánh giá: 71 (câu không-refusal có citation khớp được).

## Phân tích lỗi — câu hit@5=0 với best config (0 câu)

Không có câu nào trượt hoàn toàn ở top-k với best config.