# Research Questions — trả lời bằng số liệu thật (Phase 12)

RQ1-RQ5 theo `docs/llmops_thesis_blueprint.md` mục 1.6, đối chiếu với 6 thực nghiệm thật.

## RQ1 — Chunking + retrieval config nào tối ưu cho RAG trên văn bản quy chế tiếng Việt có cấu trúc?

**Trả lời đầy đủ, có số liệu.** `structure_aware` chunking (tách theo "Điều N.", giữ nguyên Khoản) thắng cả 4 strategy đã thử (fixed/recursive/structure_aware/parent_child) — recall@5=0.906, nDCG@5=0.787, hơn hẳn recursive (0.857/0.686) — `results_chunking_ablation.md`. Retrieval: `hybrid_dbsf` (Distribution-Based Score Fusion, prefetch=40) thắng cả 8 config đã thử (dense/sparse/hybrid_rrf/hybrid_dbsf, có/không rerank) — recall@5=0.932, nDCG@5=0.815, đạt target 0.85 — `results_retrieval_reranking.md`. Reranker (Gemini listwise) KHÔNG đáng đánh đổi latency (p95 61s khi bị rate-limit thật) dù có cải thiện nhẹ chất lượng ở mẫu lớn hơn — quyết định tắt vẫn đúng nhưng vì lý do latency, không phải chất lượng.

Config production: `hybrid_dbsf_v2` (`config/retrieval.yaml`), `structure_aware` chunking (`config/ingest.yaml`).

## RQ2 — Prompt và model/provider nào cân bằng chất lượng–chi phí–độ trễ tốt nhất?

**Trả lời đầy đủ về prompt, giới hạn thật về model/provider.** Prompt: `p7_citation_complete_safe_v1` là production sau 8 vòng lặp thật (p0→p7, cộng p8 thử-và-loại ở Phase 11) — refusal_accuracy=0.90, citation_accuracy=0.838, hallucination=0.10 trên smoke set sạch (`results_prompt_comparison_p8.md`, `results_prompt_p8_citation_multipart_v1_vs_p7.md`). Model/provider: dự án CHƯA BAO GIỜ có key OpenAI/Anthropic — so sánh chỉ khả thi trong phạm vi thật có (Gemini 2 tier + Ollama local), xem `results_model_provider_comparison.md` — **gemini-3.1-flash-lite thắng rõ trade-off** (ngang chất lượng flash-preview, rẻ hơn ~5 lần, nhanh hơn ~10 lần), qwen2.5:7b (Ollama) kém nhất mọi trục nhưng vẫn đáng giữ làm lưới an toàn reliability (cost=0, không downtime hoàn toàn).

**Trả lời một phần có chủ đích**: không thể kết luận về GPT-5/Claude như blueprint gốc dự tính — đây là giới hạn tài nguyên thật (không có key), không phải thiếu sót thực hiện.

## RQ3 — Quality gate có phát hiện & chặn regression không?

**Trả lời đầy đủ, có số liệu.** `results_quality_gate_effectiveness.md` (Phase 12) — 16 kịch bản giả lập thật (tái dùng fixture Phase 9): **Recall=1.000, Precision=1.000** (9/9 thay đổi xấu bị chặn đúng, 0 false positive trên 7 thay đổi tốt/cảnh báo). Gate cũng phân biệt đúng 3 mức PASS/WARN/BLOCK (không chỉ nhị phân) và phát hiện cả regression tương đối (giảm > margin dù vẫn trên ngưỡng tuyệt đối — kịch bản `gradual_prompt_drift_within_floor`). Gate latency không đáng kể (p95=0.011ms, hàm thuần offline). Verify sống thêm: CI thật đã BLOCK đúng 1 lần vì hallucination_rate vượt ngưỡng thật (CHECKLIST Phase 9/CI live run).

## RQ4 — Observability/trace có đủ tín hiệu phân loại nguyên nhân gốc lỗi RAG không?

**Trả lời có sắc thái — CÓ, nhưng độ chính xác phụ thuộc ngữ cảnh sử dụng.** `results_error_classification.md` (Phase 12) — classifier rule-based (`src/feedback/classifier.py`, Phase 11) áp lên 107 lỗi thật (298 câu, full eval) cho phân bố hallucination=76.6%/citation_error=12.1%/refusal_error=9.3%/provider_error=1.9%. Self-review 25 mẫu: **accuracy=40.0%** — NHƯNG phát hiện quan trọng: 14/15 lần sai đều do thiếu tín hiệu `citation_accuracy` (chỉ có ở ngữ cảnh eval có ground truth, KHÔNG có trong feedback sản xuất thật — mục đích chính classifier phục vụ). Với ngữ cảnh feedback thật (không có ground truth), trace CÓ đủ tín hiệu hữu ích thật (`invalid_citations`, `refusal`, `fallback_hop`, `error_labels`) để phân loại 4/9 nhãn một cách đáng tin (citation_error do trích sai chunk_id thật, provider_error do fallback thật, refusal_error do cờ refusal sai thật) — 40% là cận dưới đo trong ngữ cảnh KHÔNG PHẢI mục đích thiết kế, không phải con số đại diện cho use case thật.

## RQ5 — Có thể giảm chi phí/độ trễ mà vẫn giữ chất lượng bằng cache/compression/routing/feedback không?

**Trả lời có, với caveat mẫu nhỏ.** `results_optimization_o1_o8.md` (n=15) — semantic cache tiết kiệm 100% cost+latency trên câu hỏi lặp lại (cơ chế đúng, giá trị thật phụ thuộc tỷ lệ lặp câu hỏi trong traffic thật — chưa đo được ở scale). Context compression (O3) có citation_accuracy CAO NHẤT trong mẫu (0.85, thắng cả baseline 0.792) và cost thấp nhất — nhưng n=15 quá nhỏ để kết luận chắc, cần chạy lại ở scale lớn hơn. Dynamic top-k và model routing không cho thấy cải thiện rõ rệt ở mẫu này. Feedback-improved (O8, p8 prompt): **kết quả THẬT LÀ TIÊU CỰC** — citation_accuracy giảm (0.838→0.775), không activate — một vòng cải tiến hoàn chỉnh với kết luận trung thực, không phải mọi vòng cải tiến đều phải thành công.

## Tổng kết mức độ trả lời

| RQ | Mức độ | Ghi chú |
|---|---|---|
| RQ1 | Đầy đủ | Số liệu thật, kết luận rõ ràng |
| RQ2 | Một phần | Đầy đủ về prompt; model/provider giới hạn bởi không có key OpenAI/Anthropic |
| RQ3 | Đầy đủ | Recall=Precision=1.000 trên 16 kịch bản |
| RQ4 | Có sắc thái | 40% trên eval-retroactive, nhưng có giải thích cấu trúc rõ ràng cho use case thật |
| RQ5 | Có caveat | Cơ chế đúng, độ lớn cải thiện cần đo thêm ở scale lớn hơn n=15 |
