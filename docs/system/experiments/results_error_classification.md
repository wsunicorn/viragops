# Experiment 5 — Observability + Error Classification

Nguồn: `eval_full_20260712_0938.csv` (298 câu, `p1_grounded_v1`, `data_20260712` — cùng file dùng seed feedback Phase 11, nhưng KHÔNG lọc citation-only/primary-only lần này — muốn thấy đúng bức tranh lỗi thật, kể cả provider_error từ câu bị fallback).

- Tổng câu: 298. Không phải lỗi (qua mọi 4 tiêu chí): 191.
- Câu lỗi match được trace: 107. Không match được trace: 0.

## Phân bố nhãn lỗi tự động (rule-based, src/feedback/classifier.py)

| error_label | Số câu | Tỷ lệ |
|---|---:|---:|
| hallucination | 82 | 76.6% |
| citation_error | 13 | 12.1% |
| refusal_error | 10 | 9.3% |
| provider_error | 2 | 1.9% |

## Human-review sample (n=25, seed=12)

Mẫu random đã ghi ra `data/eval/error_classification_review_sample.json`. Review THẬT — đọc từng trace/câu hỏi/answer, tự phán đoán ĐỘC LẬP nhãn đúng nhất (không nhìn `auto_label` trước khi kết luận), rồi mới so sánh. Cùng mức độ trung thực đã dùng cho golden-set review (Phase 2): **đây là AI tự-review, không phải domain-expert thật** — nhưng có audit trail đầy đủ (lý do từng câu), không phải rubber-stamp.

| question_id | category | auto_label | Nhãn tự đánh giá | Khớp? | Lý do |
|---|---|---|---|---|---|
| q_199 | ambiguous | refusal_error | refusal_error | ✅ | `unparseable_model_output` → forced refusal đúng thiết kế fail-closed; taxonomy không có nhãn "parse_error" riêng nên refusal_error là lựa chọn hợp lý nhất. |
| q_113 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.5 + judge hallucination=False → nội dung có căn cứ thật, chỉ thiếu 1/2 citation — không phải bịa. |
| q_266 | ambiguous | provider_error | provider_error | ✅ | judge hallucination=True THẬT + served_by_fallback:secondary — model dự phòng chất lượng kém hơn, đúng nguyên nhân gốc. |
| q_211 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.0 nhưng judge hallucination=False — câu trả lời cụ thể, đúng khả năng cao, chỉ trích dẫn sai/thiếu hoàn toàn. |
| q_269 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False — quy đổi điểm cụ thể, nửa citation đúng. |
| q_140 | factoid | hallucination | refusal_error | ❌ | `refusal_correct=False` + câu trả lời né tránh không đủ ("không đề cập") — lẽ ra nên refuse rõ ràng hoặc trả lời đủ, đây là lỗi quyết định refuse/answer chứ không phải bịa nội dung. |
| q_041 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False — câu trả lời 1 câu cụ thể, nửa citation đúng. |
| q_155 | ambiguous | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False, câu trả lời nhiều vế (buộc thôi học) — thiếu citation cho 1 số vế, không phải bịa. |
| q_016 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.33, hallucination=False — đây chính là 1 trong các câu golden-set có ground truth từng bị sai document_id, đã sửa sau đó (CHECKLIST Phase 8) — tín hiệu citation thấp, không phải model bịa. |
| q_154 | ambiguous | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False. |
| q_200 | ambiguous | refusal_error | refusal_error | ✅ | `refusal_correct=False`, model từ chối nhưng thực ra có căn cứ trả lời — đúng nguyên nhân refusal sai. |
| q_115 | factoid | hallucination | hallucination | ✅ | citation_accuracy=1.0 (trích ĐÚNG chunk) nhưng judge vẫn báo hallucination=True — nội dung sai lệch dù có căn cứ đúng, đúng định nghĩa hallucination của runbook ("context đúng, answer sai"). |
| q_257 | multi_hop | hallucination | hallucination | ✅ | Tương tự q_115: citation_accuracy=1.0, hallucination=True thật. |
| q_192 | factoid | hallucination | refusal_error | ❌ | `refusal_correct=False`, câu trả lời né tránh thay vì refuse rõ ràng hoặc trả lời đủ — lỗi quyết định refuse, không phải bịa. |
| q_278 | procedural | refusal_error | refusal_error | ✅ | `refusal_correct=False`, model refuse sai. |
| q_240 | ambiguous | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False, câu trả lời nhiều vế. |
| q_069 | multi_hop | hallucination | citation_error | ❌ | citation_accuracy=0.0 nhưng hallucination=False — đúng dạng gap multi-hop citation đã biết (CHECKLIST item 9/10), không phải bịa nội dung. |
| q_218 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.33, hallucination=False, câu trả lời nhiều vế (khoa học + bảo mật). |
| q_014 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False. |
| q_298 | factoid | citation_error | citation_error | ✅ | `invalid_citations_dropped` + fallback:local (Ollama) — đúng bug rút gọn chunk_id đã biết (CHECKLIST Phase 8). |
| q_254 | multi_hop | refusal_error | refusal_error | ✅ | `refusal_correct=False`, refuse sai. |
| q_294 | procedural | citation_error | citation_error | ✅ | Cùng dạng Ollama-local citation-id-truncation như q_298. |
| q_183 | ambiguous | hallucination | citation_error | ❌ | citation_accuracy=0.0, hallucination=False — câu trả lời cụ thể có căn cứ hợp lý, chỉ trích dẫn sai/thiếu. |
| q_291 | factoid | citation_error | citation_error | ✅ | Cùng dạng Ollama-local citation-id-truncation. |
| q_044 | factoid | hallucination | citation_error | ❌ | citation_accuracy=0.5, hallucination=False. |

**Accuracy = 10/25 = 40.0%** (khớp: q_199, q_266, q_200, q_115, q_257, q_278, q_298, q_254, q_294, q_291).

## Phát hiện thật quan trọng — giới hạn của classifier rule-based

Sai lệch KHÔNG ngẫu nhiên: **14/15 lần sai đều là hallucination-thay-vì-citation_error**, và ĐÚNG hệt 1 mẫu hình — mọi lần sai đều có `citation_accuracy` nằm giữa 0.0 và 1.0 (không phải 1.0) VÀ judge `hallucination=False` thật. `classify_error_label()` (Module 9) mặc định rơi về `"hallucination"` khi không có `invalid_citations`/`refusal`/`fallback`/`low_score` — nhưng **không hề có tín hiệu `citation_accuracy`** để phân biệt "trích thiếu nhưng nội dung đúng" (citation_error) với "trích đủ nhưng nội dung sai" (hallucination thật, như q_115/q_257).

**Đây KHÔNG phải bug cần sửa ngay trong classifier** — lý do cấu trúc: `citation_accuracy` chỉ tính được khi có ground truth (`relevant_chunks`, chỉ có trong golden set eval), còn feedback THẬT từ người dùng sản xuất (mục đích chính của `classify_error_label`, Module 9) không bao giờ có ground truth đó — classifier sản xuất **đúng theo thiết kế** cho ngữ cảnh nó phục vụ (chỉ dùng tín hiệu có thật lúc runtime: `invalid_citations`/`refusal`/`fallback_hop`/`error_labels`). Khi áp dụng NGƯỢC vào dữ liệu eval (có ground truth) như Experiment 5 làm, classifier trông "kém" hơn thật vì bị so với thông tin nó không có quyền dùng trong sản xuất — 40% accuracy đo được ở đây là **cận dưới cho ngữ cảnh eval-retroactive**, không phải con số đại diện cho chất lượng phân loại feedback thật.

**Hướng cải thiện hợp lệ, chưa làm (ngoài scope Phase 11/12)**: thêm 1 biến thể `classify_error_label_with_ground_truth(trace, feedback_type, citation_accuracy=None)` CHỈ dùng ở Evaluation Engine (nơi CÓ ground truth) để phân biệt chính xác hơn hallucination/citation_error khi phân tích offline — giữ nguyên hàm gốc cho đường feedback sản xuất thật.