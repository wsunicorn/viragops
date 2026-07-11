# Kết quả so sánh prompt P0-P5 (smoke set)

> Run `promptcmp_20260711_1408` — 12 câu smoke (12 id cố định trong `scripts/run_prompt_comparison.py`), retrieval dùng chung (`hybrid_dbsf_v2`), gateway tier theo từng prompt (balanced). Metric đo được KHÔNG cần LLM-judge; faithfulness/answer-relevance đầy đủ chờ Evaluation Engine (Phase 8).

| version | parse ok | refusal acc | citation valid | grounded cite | avg tokens | avg gen ms |
|---|---:|---:|---:|---:|---:|---:|
| p1_grounded_v1 **(best)** | 1.00 | 1.00 | 1.00 | 1.00 | 83.4 | 1159 |
| p5_concise_v1 | 1.00 | 1.00 | 1.00 | 0.88 | 81.2 | 1154 |
| p3_refusal_aware_v1 | 1.00 | 0.75 | 1.00 | 1.00 | 103.6 | 1349 |
| p4_self_check_v1 | 1.00 | 0.50 | 1.00 | 1.00 | 111.8 | 1380 |
| p0_naive_v1 | 1.00 | 0.50 | 1.00 | 1.00 | 120.8 | 1256 |
| p2_citation_first_v1 | 1.00 | 0.00 | 1.00 | 0.88 | 100.8 | 1237 |

- Best (refusal+grounded, tie-break ít token): **p1_grounded_v1**.
- Mọi version đã được gán `eval_result_id=promptcmp_20260711_1408` trong registry.
- CSV: `data/experiments/promptcmp_20260711_1408.csv`.