# So sánh 6 prompt variant qua Evaluation Engine thật (Phase 8, 2026-07-14)

> Item 10 remediation ("re-test p0/p2/p3/p4/p5 qua Evaluation Engine thật"). Phase 6's
> `results_prompt_comparison.md` so 6 variant trên 12 câu smoke cố định, KHÔNG có
> LLM-judge (chỉ đo parse/refusal/citation-valid xác định được). Đây là lần đầu cả 6
> variant được chạy qua **Evaluation Engine đầy đủ** (Phase 8: retrieval thật + LLM-judge
> 4 tiêu chí + category breakdown), mỗi variant 50 câu smoke stratified, cùng ngày
> (2026-07-14), cùng `data_version=data_20260713`, `retrieval_config_id=hybrid_dbsf_v2`,
> **0% fallback contamination** ở cả 6 lần chạy (mọi câu qua Gemini primary) — số liệu
> sạch, so sánh được trực tiếp với nhau.

| Prompt | Recall@5 | Faithfulness | Answer Rel. | Citation Acc | Refusal Acc | Hallucination | p95 latency | Error rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| p0_naive_v1 (baseline yếu, cố ý) | 0.905 | 0.841 | 0.976 | 0.779 | 0.740 | 0.293 | 1852ms | 0.080 |
| p2_citation_first_v1 | 0.905 | 0.909 | 0.943 | 0.814 | 0.780 | 0.091 | 1792ms | 0.040 |
| p3_refusal_aware_v1 | 0.905 | 0.940 | 0.964 | 0.796 | 0.860 | 0.095 | 1806ms | 0.080 |
| p4_self_check_v1 | 0.905 | 0.927 | 0.976 | 0.796 | 0.880 | 0.098 | 1948ms | 0.100 |
| **p5_concise_v1** | 0.905 | **0.963** | 0.950 | 0.819 | 0.900 | **0.075** | 2129ms | **0.000** |
| **p7_citation_complete_safe_v1 (production)** | 0.905 | 0.950 | 0.963 | **0.838** | 0.900 | 0.100 | **1287ms** | **0.000** |

Target: Recall@5≥0.85, Faithfulness≥0.85, Answer Rel.≥0.80, Citation Acc≥0.85,
Refusal Acc≥0.90, Hallucination≤0.05, p95≤6000ms, Error rate≤0.01.

## Đọc kết quả

- **Recall@5 giống hệt (0.905) ở cả 6 variant** — đúng như kỳ vọng: retrieval hoàn
  toàn độc lập với prompt, chỉ prompt (tầng generation) mới đổi giữa các lần chạy.
- **p0_naive_v1 xác nhận đúng vai trò baseline yếu có chủ đích**: Refusal Accuracy
  thấp nhất (0.740), Hallucination cao nhất (0.293), Error rate cao (0.080) — không
  ràng buộc grounding/refusal nào, đúng thiết kế gốc (xem `src/promptops/templates.py`).
- **p2/p3/p4 đều cụm dưới p7 ở Refusal Accuracy (0.780-0.880, dưới target 0.90)** —
  khớp kết luận Phase 6 (p2 "chọn nguồn trước rồi viết" phản tác dụng với refusal;
  p3 dù thiết kế chuyên refusal vẫn không vượt được p1/p7).
- **Phát hiện đáng chú ý nhất: p5_concise_v1 cạnh tranh RẤT SÁT với p7, thậm chí
  THẮNG 2 tiêu chí** — Faithfulness 0.963 (> p7's 0.950), Hallucination 0.075 (< p7's
  0.100), Refusal Accuracy hoà 0.900, Error rate 0.000 (hoà p7). Chỉ thua ở Citation
  Accuracy (0.819 vs 0.838 — vẫn dưới target 0.85 ở cả 2) và p95 latency cao hơn
  (2129ms vs 1287ms, nhưng cả 2 đều xa dưới ngân sách NFR-002 6000ms nên không phải
  vấn đề vận hành thật). Phase 6 đã gợi ý p5 là "ứng viên cost-aware chờ Phase 8 xác
  nhận chất lượng đầy đủ" — **giờ đã xác nhận: p5 KHÔNG đánh đổi chất lượng đáng kể để
  lấy giảm token**, và ở 2 tiêu chí faithfulness/hallucination còn tốt hơn bản
  production hiện tại.
- **Không variant nào trong 5 variant re-test vượt được Citation Accuracy của p7** —
  hợp lý vì p7 là kết quả của 2 vòng sửa prompt chuyên biệt cho vấn đề citation
  (p1→p6→p7, xem CHECKLIST Phase 8 "Sửa citation accuracy multi-hop/ambiguous").

## Kết luận + khuyến nghị

Dữ liệu này **xác nhận, không thay đổi** quyết định p7 đang production — p7 vẫn thắng
rõ ở Citation Accuracy (tiêu chí quan trọng nhất cho domain quy chế/trích dẫn) và có
latency thấp nhất. **Không tự động activate variant nào khác** — theo đúng policy dự
án (activation cần eval_result_id + xác nhận người dùng qua AskUserQuestion, xem
`src/promptops/registry.py`).

Phát hiện p5 mạnh ở faithfulness/hallucination là **input thật cho 1 hướng cải thiện
tương lai** (chưa làm trong lần này): thử kết hợp quy tắc citation-completeness của
p7 với phong cách súc tích của p5 ("p8 = p7 rules + p5 style") — có thể đạt được cả 2
mục tiêu thay vì phải đánh đổi. Đây là gợi ý dựa trên số liệu thật, không phải suy
đoán, nhưng CHƯA implement — để dành cho lần làm tiếp theo nếu người dùng muốn.

## Nguồn số liệu

- `data/eval/eval_smoke_20260714_0817_summary.json` (p0)
- `data/eval/eval_smoke_20260714_0827_summary.json` (p2)
- `data/eval/eval_smoke_20260714_0835_summary.json` (p3)
- `data/eval/eval_smoke_20260714_0844_summary.json` (p4)
- `data/eval/eval_smoke_20260714_0852_summary.json` (p5)
- `data/eval/eval_smoke_20260714_0320_summary.json` (p7, production — chạy trước đó
  cùng ngày, xem CHECKLIST Phase 9)
- Report đầy đủ từng variant: `results_prompt_p8_<version>.md`
