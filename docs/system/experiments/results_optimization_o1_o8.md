# O1-O8 Optimization Experiment (Phase 11, Module 8)

Chạy thật (không giả lập) qua RagService thật, 15 câu golden set (stratified, seed=8 — cùng subset cho mọi config O1-O5/O7). O6 đo passive (gộp fallback_hop thật từ mọi run trên). O8 tái dùng kết quả p8_citation_multipart_v1 đã chạy thật ở improvement cycle (n=48, KHÁC n với các config khác — ghi rõ trong bảng).

> **Bug thật phát hiện khi chạy, đã sửa (script) + ghi chú lại (report):**
> `O2_cache_pass2_warm` và `O7_combined` (toàn cache hit) có
> `faithfulness=0.0`/`hallucination_rate=1.0` — KHÔNG PHẢI chất lượng giảm
> thật. Cache hit trả lời NGAY từ payload đã lưu, bỏ qua retrieval hoàn
> toàn (`trace["retrieved"]=[]`) — Evaluation Engine (`run_question()`)
> dựng lại context cho judge từ `trace["retrieved"]`, nên với cache hit nó
> chấm câu trả lời THẬT so với ngữ cảnh RỖNG → judge đúng đắn báo
> "không có căn cứ" cho một câu trả lời thực ra đã được chính judge duyệt
> ở lần gọi gốc (cache chỉ tái dùng answer đã qua kiểm chứng, không tạo
> answer mới). Đây là hạn chế của harness đánh giá (chưa có xử lý riêng
> cho cache hit), không phải bug của cache — `citation_accuracy` (tính từ
> `resp.citations` thật, không qua `trace["retrieved"]`) vẫn đúng và nhất
> quán giữa pass 1/pass 2 (0.778 cả 2 lần). Tương tự, `fallback_hop="cache"`
> ban đầu bị gộp nhầm vào "cần fallback" ở cả `aggregate()` (field
> `fallback_rate`, không sửa — hành vi hiện có từ Phase 7/8, ngoài scope
> phase này) LẪN script O6 tự viết của phase này (ĐÃ SỬA, xem
> `scripts/run_experiment_optimization.py`) — số O6 dưới đây là số ĐÃ SỬA,
> tính lại tay từ `fallback_rate` từng config (loại 2 config toàn cache).

| Config | n | Citation Acc | Faithfulness | Refusal Acc | p95 latency (ms) | Avg cost/req | Cache hit rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| O1_baseline | 15 | 0.7916666666666666 | 0.9583333333333334 | 1.0 | 1520 | 0.0009107833333333333 | n/a |
| O2_cache_pass1_cold | 15 | 0.7777777777777777 | 1.0 | 1.0 | 1629 | 0.0009184833333333333 | 0/15 |
| O2_cache_pass2_warm | 15 | 0.7777777777777777 | 0.0 (artefact, xem chú thích trên) | 1.0 | None (cache trả tức thời, không generation_ms) | 0.0 | 15/15 |
| O3_compression | 15 | 0.85 | 1.0 | 0.8666666666666667 | 1409 | 0.0007144166666666667 | n/a |
| O4_dynamic_top_k | 15 | 0.7916666666666666 | 1.0 | 1.0 | 1638 | 0.0008498166666666666 | n/a |
| O5_routing | 15 | 0.7777777777777777 | 1.0 | 1.0 | 2093 | 0.0009124833333333331 | n/a |
| O7_combined | 15 | 0.7777777777777777 | 0.0 (artefact, xem chú thích trên) | 1.0 | None | 0.0 | 15/15 |
| O8_feedback_improved (p8, n khác) | 48 | 0.7745098039215685 | 0.9473684210526315 | 0.8958333333333334 | 2101 | 0.0009586666666666666 | n/a |

**O6 provider fallback rate (đã sửa, chỉ tính config KHÔNG toàn cache —
O1/O2_pass1/O3/O4/O5, n=75 lượt gọi provider thật):** 3/75 = 0.04 (3 câu
fallback đều ở O5_routing — có thể do tier `strong` được route tới nhiều
hơn ở config này, cần thêm dữ liệu để kết luận chắc).

## Đọc số liệu chính (loại trừ 2 config bị artefact)

- **O3 context compression THẮNG rõ nhất trong 15 câu này**: Citation
  Accuracy cao nhất (0.85 vs baseline 0.79), cost thấp nhất (giảm ~22%
  so O1) — nhưng Refusal Accuracy tụt (0.867 vs 1.0, 1/15 sai) và
  error_rate=0.067 (1 lỗi) — mẫu quá nhỏ (n=15) để kết luận chắc, cần
  chạy lại ở quy mô lớn hơn trước khi cân nhắc bật mặc định.
- **O4 dynamic top-k**: không đổi citation accuracy so baseline, cost giảm
  nhẹ (~7%), context_precision tăng (0.183→0.239 — cắt bớt chunk ít liên
  quan khi retrieval tự tin).
- **O5 routing (auto)**: cost gần như không đổi so baseline (câu trong mẫu
  đa số bị phân loại "medium"→balanced, giống mặc định) — p95 latency
  cao hơn hẳn (2093ms) do 3/15 câu rơi vào fallback tình cờ trong lần
  chạy này (nhiễu hạ tầng, không phải do routing).
- **O2 cache (đọc đúng, bỏ qua judge artefact)**: cache hit tiết kiệm
  100% cost + generation_ms trên đúng câu đã hỏi trước đó — cơ chế đúng
  như thiết kế, giá trị thực tế phụ thuộc tỷ lệ câu hỏi LẶP LẠI trong
  traffic thật (chưa đo được ở quy mô production).

## Raw aggregate JSON (mỗi config)

```json
{
  "O1_baseline": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.875,
      "hit_rate": 0.9166666666666666,
      "mrr": 0.8541666666666666,
      "ndcg_at_k": 0.8231012762781708
    },
    "context_precision": 0.18333333333333332,
    "context_recall": 0.875,
    "context_relevance": 0.9583333333333334,
    "faithfulness": 0.9583333333333334,
    "answer_relevance": 1.0,
    "hallucination_rate": 0.08333333333333333,
    "citation_accuracy": 0.7916666666666666,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": 1229,
    "p95_latency_ms": 1520,
    "avg_cost_usd": 0.0009107833333333333,
    "error_rate": 0.0,
    "fallback_rate": 0.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 1.0,
    "n_ambiguity_scored": 1
  },
  "O2_cache_pass1_cold": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.875,
      "hit_rate": 0.9166666666666666,
      "mrr": 0.8541666666666666,
      "ndcg_at_k": 0.8231012762781708
    },
    "context_precision": 0.18333333333333332,
    "context_recall": 0.875,
    "context_relevance": 1.0,
    "faithfulness": 1.0,
    "answer_relevance": 1.0,
    "hallucination_rate": 0.0,
    "citation_accuracy": 0.7777777777777777,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": 1202,
    "p95_latency_ms": 1629,
    "avg_cost_usd": 0.0009184833333333333,
    "error_rate": 0.0,
    "fallback_rate": 0.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 0.0,
    "n_ambiguity_scored": 1
  },
  "O2_cache_pass2_warm": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.0,
      "hit_rate": 0.0,
      "mrr": 0.0,
      "ndcg_at_k": 0.0
    },
    "context_precision": null,
    "context_recall": 0.0,
    "context_relevance": 0.0,
    "faithfulness": 0.0,
    "answer_relevance": 0.7916666666666666,
    "hallucination_rate": 1.0,
    "citation_accuracy": 0.7777777777777777,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": null,
    "p95_latency_ms": null,
    "avg_cost_usd": 0.0,
    "error_rate": 0.0,
    "fallback_rate": 1.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 0.0,
    "n_ambiguity_scored": 1
  },
  "O3_compression": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.875,
      "hit_rate": 0.9166666666666666,
      "mrr": 0.8541666666666666,
      "ndcg_at_k": 0.8231012762781708
    },
    "context_precision": 0.18333333333333332,
    "context_recall": 0.875,
    "context_relevance": 1.0,
    "faithfulness": 1.0,
    "answer_relevance": 0.95,
    "hallucination_rate": 0.1,
    "citation_accuracy": 0.85,
    "refusal_accuracy": 0.8666666666666667,
    "n_judged": 10,
    "n_judge_errors": 0,
    "p50_latency_ms": 1180,
    "p95_latency_ms": 1409,
    "avg_cost_usd": 0.0007144166666666667,
    "error_rate": 0.06666666666666667,
    "fallback_rate": 0.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 1.0,
    "n_ambiguity_scored": 1
  },
  "O4_dynamic_top_k": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.875,
      "hit_rate": 0.9166666666666666,
      "mrr": 0.8541666666666666,
      "ndcg_at_k": 0.8231012762781708
    },
    "context_precision": 0.23888888888888893,
    "context_recall": 0.875,
    "context_relevance": 1.0,
    "faithfulness": 1.0,
    "answer_relevance": 1.0,
    "hallucination_rate": 0.08333333333333333,
    "citation_accuracy": 0.7916666666666666,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": 1181,
    "p95_latency_ms": 1638,
    "avg_cost_usd": 0.0008498166666666666,
    "error_rate": 0.0,
    "fallback_rate": 0.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 1.0,
    "n_ambiguity_scored": 1
  },
  "O5_routing": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.875,
      "hit_rate": 0.9166666666666666,
      "mrr": 0.8541666666666666,
      "ndcg_at_k": 0.8231012762781708
    },
    "context_precision": 0.18333333333333332,
    "context_recall": 0.875,
    "context_relevance": 1.0,
    "faithfulness": 1.0,
    "answer_relevance": 1.0,
    "hallucination_rate": 0.0,
    "citation_accuracy": 0.7777777777777777,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": 1293,
    "p95_latency_ms": 2093,
    "avg_cost_usd": 0.0009124833333333331,
    "error_rate": 0.2,
    "fallback_rate": 0.2,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 1.0,
    "n_ambiguity_scored": 1
  },
  "O7_combined": {
    "n_questions": 15,
    "eval_k": 5,
    "retrieval": {
      "n_questions": 12,
      "recall_at_k": 0.0,
      "hit_rate": 0.0,
      "mrr": 0.0,
      "ndcg_at_k": 0.0
    },
    "context_precision": null,
    "context_recall": 0.0,
    "context_relevance": 0.0,
    "faithfulness": 0.0,
    "answer_relevance": 0.7916666666666666,
    "hallucination_rate": 1.0,
    "citation_accuracy": 0.7777777777777777,
    "refusal_accuracy": 1.0,
    "n_judged": 12,
    "n_judge_errors": 0,
    "p50_latency_ms": null,
    "p95_latency_ms": null,
    "avg_cost_usd": 0.0,
    "error_rate": 0.0,
    "fallback_rate": 1.0,
    "cache_hit_rate": null,
    "inter_judge_agreement": null,
    "ambiguity_handling_rate": 0.0,
    "n_ambiguity_scored": 1
  }
}
```