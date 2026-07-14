# p8_citation_multipart_v1 vs p7 — improvement cycle (Phase 11 Feedback Loop)

## Nguồn gốc

Feedback Loop (Module 9) thật, không giả lập:
`scripts/seed_feedback_from_eval.py` seed 26 feedback record `source=eval_seed`
từ `data/eval/eval_full_20260712_0938.csv` (298 câu, `p1_grounded_v1`, đường
sạch `fallback_hop=primary`) — 2 cluster thật:

| Cluster | error_label | category | size |
|---|---|---|---:|
| TICKET-001 | citation_error | multi_hop | 17 |
| TICKET-002 | citation_error | ambiguous | 9 |

Backlog đầy đủ: `results_improvement_backlog_20260714_1354.md`.

## Giả thuyết p8

p6/p7's rule 3 ĐÃ yêu cầu "trả lời đầy đủ từng vế và trích dẫn riêng cho
từng vế" nhưng chỉ là một quy tắc TUYÊN BỐ, không có bước kiểm tra —
`p8_citation_multipart_v1` (`src/promptops/templates.py`) thêm 1 quy tắc
self-check tường minh (rule 8): trước khi xuất kết quả, liệt kê từng
vế/từng ý trong câu hỏi, xác nhận mỗi vế có citation, bổ sung/nêu rõ nếu
thiếu.

## Kết quả THẬT (2026-07-14) — giả thuyết SAI, không cải thiện

Smoke eval 48/50 câu (2 lỗi mạng transient), so với p7's baseline
smoke run (50 câu, cùng cấu hình data_version/index_version/retrieval_config,
`eval_smoke_20260714_0320_summary.json`):

| Metric | p7 (baseline) | p8_citation_multipart_v1 | Δ |
|---|---:|---:|---|
| Citation Accuracy | 0.838 | **0.775** | **-0.063 (TỆ HƠN — đúng chỉ số nhắm sửa)** |
| Refusal Accuracy | 0.900 | 0.896 | -0.004 |
| Faithfulness | 0.950 | 0.947 | -0.003 |
| Answer Relevance | 0.963 | 0.974 | +0.011 |
| Hallucination Rate | 0.100 | 0.079 | +0.021 (tốt hơn) |
| p95 latency | 1287 ms | **2101 ms** | **+63% (TỆ HƠN đáng kể)** |
| Avg cost/req | $0.000918 | $0.000959 | +4% |

**Quality Gate: BLOCK** (`results_quality_gate_20260714_1405.md`,
`scripts/check_gate.py --eval-run eval_smoke_20260714_1403_summary.json
--baseline eval_smoke_20260714_0320_summary.json`):
- `[CRITICAL/threshold] hallucination_rate=0.0789 > max 0.05`
- `[CRITICAL/threshold] refusal_accuracy=0.8958 < min 0.9`
- `[CRITICAL/regression] p95_latency_seconds tăng 0.814s so baseline, vượt max_quality_drop`
- `[WARNING/threshold] citation_accuracy=0.7745 < min 0.85`

## Phân tích — vì sao thất bại

Rule 8 (self-check) là một bước TƯ DUY THÊM trong cùng 1 lệnh gọi, không
phải một lệnh gọi thứ 2 (khác p4_self_check_v1's thiết kế 3-bước cũng đã
thất bại tương tự ở Phase 6 — refusal chỉ 0.75). Giả thuyết hợp lý nhất:
thêm một quy tắc dài + yêu cầu "tự liệt kê rồi tự sửa" khiến model output
dài hơn (giải thích trực tiếp cho p95 latency +63%) mà KHÔNG thực sự sửa
được hành vi bỏ sót citation — có thể còn làm model kém tập trung hơn vào
quy tắc citation gốc (rule 2-4) vì phải xử lý thêm 1 tầng chỉ dẫn. Cùng
bài học đã thấy ở `top_k_after` (CHECKLIST Phase 8) và multi-hop per-hop
retrieval (CHECKLIST item 9): **thêm ràng buộc/tầng xử lý KHÔNG tự động
cải thiện citation accuracy — phải đo thật, không suy luận từ thiết kế**.

## Quyết định

**KHÔNG activate p8_citation_multipart_v1** — giữ nguyên
`p7_citation_complete_safe_v1` làm production, đúng chính sách đã áp dụng
nhất quán cho p6/p7 (chỉ activate khi có số liệu thật CHỨNG MINH cải
thiện, không suy luận). `p8_citation_multipart_v1` giữ nguyên trong
registry ở status `testing` làm tài liệu cho thí nghiệm đã thử.

Gap citation accuracy multi_hop/ambiguous **vẫn còn treo thật** — 2 hướng
đã thử và không thắng baseline (per-hop retrieval, CHECKLIST item 9; self-
check prompt, tài liệu này) đều bị loại bằng số liệu thật. Hướng khả dĩ
còn lại, chưa thử: sửa PARSER/citation.py để tự động phát hiện câu hỏi
nhiều vế và validate số lượng citation tối thiểu theo số vế phát hiện
được (kiểm tra sau khi model trả lời, không dựa vào model tự giác trong
prompt).
