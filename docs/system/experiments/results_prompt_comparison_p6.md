# Kết quả so sánh: p1_grounded_v1 (active) vs p6_citation_complete_v1 (candidate)

> Sinh thủ công từ 3 cặp chạy `scripts/run_evaluation.py --prompt-version ...`
> lúc 2026-07-12 (~10:00-10:25 UTC), `--no-judge` (chỉ đo retrieval/citation/
> refusal — không tốn quota judge). `eval_result_id=eval_citation_cmp_20260712_1010`
> đã ghi cho cả 2 version trong registry. **p6 CHƯA được activate** — chờ
> quyết định của user (xem CHECKLIST Phase 8 "Chưa tốt").

## Vì sao có candidate này

Full eval 300 câu (2026-07-12, `results_evaluation_full.md`) đo được Citation
Accuracy thấp nhất ở multi_hop (0.625) và ambiguous (0.452) trên đường
primary sạch. Đọc failure list + trace thật cho thấy 2 nguyên nhân:
1. Model có chunk đúng trong top-5 nhưng KHÔNG trích, hoặc trích thêm chunk
   không liên quan (over-citation/wrong-pick) — vd q_129 trích nhầm "Điều 4"
   không liên quan, q_202 trích "Điều 18" thay vì "Điều 24" đã retrieve đúng.
2. Với câu nhiều vế (multi-hop) hoặc câu cần nêu nhiều trường hợp (ambiguous),
   model hay chỉ trả lời/trích 1 vế rồi bỏ sót vế còn lại.

`p6_citation_complete_v1` (`src/promptops/templates.py`) thêm 4 quy tắc cụ
thể nhắm đúng 2 nguyên nhân này vào `p1_grounded_v1` (xem template đầy đủ
trong code, `change_summary` tóm tắt).

## Kết quả — multi_hop (n=30, toàn bộ câu multi_hop có căn cứ)

| Metric | p1 (active) | p6 (candidate) | Chênh lệch |
|---|---:|---:|---:|
| Recall@5 | 0.856 | 0.856 | 0 (retrieval không đổi — đúng kỳ vọng, chỉ đổi prompt) |
| Citation Accuracy | 0.672 | **0.700** | +0.028 |
| Refusal Accuracy | 0.967 | **1.000** | +0.033 |

## Kết quả — ambiguous (n=20, toàn bộ câu ambiguous có căn cứ)

| Metric | p1 (active) | p6 (candidate) | Chênh lệch |
|---|---:|---:|---:|
| Recall@5 | 0.789 | 0.789 | 0 |
| Citation Accuracy | 0.451 | **0.535** | +0.084 |
| Refusal Accuracy | 0.900 | **1.000** | +0.100 |

## Kiểm tra hồi quy — smoke 50 câu (đủ 6 category, cùng bộ câu với `results_evaluation_smoke.md`)

| Category | n | p1 Refusal Acc | p6 Refusal Acc | p1 Citation Acc | p6 Citation Acc |
|---|---:|---:|---:|---:|---:|
| adversarial | 2 | 1.000 | 1.000 | n/a | n/a |
| ambiguous | 3 | 0.667 | 1.000 | 1.000 | 0.667 |
| factoid | 36 | 0.889 | 0.889 | 0.878 | **0.897** |
| multi_hop | 5 | 0.800 | **1.000** | 0.417 | **0.633** |
| out_of_scope | 2 | 1.000 | 1.000 | n/a | n/a |
| procedural | 2 | 1.000 | 1.000 | 1.000 | 1.000 |

Ambiguous ở bảng smoke giảm citation accuracy (1.000→0.667) nhưng **n=3 —
không đủ tin cậy** (1 câu đổi kết quả là ±33 điểm %); mẫu ambiguous lớn hơn
(n=20, bảng trên) cho kết quả NGƯỢC LẠI và đáng tin hơn (+0.084). Không
category nào có dấu hiệu hồi quy thật với cỡ mẫu đủ lớn để kết luận.

**Lưu ý vận hành khi chạy 2 lần đo sau:** cả 2 key Gemini (primary,
secondary) đã cạn quota ngày trước khi chạy các lần so sánh này — lần chạy
smoke ở trên phục vụ 100% qua **key thứ 3 mới** (`GEMINI_API_KEY_5`, thêm
2026-07-12, xem `config/litellm_config.yaml` chặng `tertiary`), KHÔNG phải
Ollama fallback (nên chất lượng vẫn phản ánh đúng Gemini, không bị nhiễu
kiểu Ollama đã thấy ở full eval). `error_rate`/`fallback_rate` trong report
gốc hiện=1.0 chỉ là nhãn ghi nhận "phục vụ bởi key phụ", không phải câu trả
lời lỗi thật — đọc kèm category breakdown mới đúng.

## Kết luận

p6 cải thiện Citation Accuracy VÀ Refusal Accuracy trên cả 2 mẫu lớn
(multi_hop, ambiguous), không thấy hồi quy đáng tin trên các category còn
lại kể cả factoid (mẫu lớn nhất, n=36, giữ nguyên/nhích lên nhẹ dù p6 thêm
quy tắc trích dẫn khắt khe hơn). Citation Accuracy vẫn CHƯA đạt target 0.85
ở cả 2 category dù đã cải thiện — đây là cải thiện thật, không phải giải
pháp triệt để; retrieval-side fix (vd re-retrieval theo từng hop cho câu
multi-hop) mới có khả năng đóng nốt phần gap còn lại.

**Khuyến nghị:** activate p6 làm active version — bằng chứng đủ để qua
được `PromptRegistry.activate()`'s yêu cầu `eval_result_id` (đã set:
`eval_citation_cmp_20260712_1010`). Quyết định activate cuối cùng để user
xác nhận (deploy production prompt vượt phạm vi "sửa citation accuracy"
ban đầu yêu cầu).
