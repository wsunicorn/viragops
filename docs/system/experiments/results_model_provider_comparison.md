# Experiment 3 (part 2) — Model/Provider Comparison

**Ràng buộc thật**: dự án CHƯA BAO GIỜ có key OpenAI/Anthropic (`config/model_gateway.yaml`'s header comment ghi rõ từ Phase 5) — so sánh GPT-5/Claude/Gemini theo blueprint gốc KHÔNG khả thi với dữ liệu thật. So sánh đúng những gì thật sự có: 2 model Gemini (khác tier, khác tốc độ/chất lượng) + 1 model local qua Ollama (không có route LiteLLM nào coi Ollama là primary — luôn là fallback cuối — nên gọi trực tiếp HTTP, dùng ĐÚNG retrieval + `build_qa_prompt()` các model Gemini dùng để so sánh công bằng).

n=10 câu (stratified, seed=8), prompt_version=`p7_citation_complete_safe_v1` (production hiện tại). Kết quả Gemini đã lọc chỉ giữ `fallback_hop=primary` (loại quota hiccup cùng ngày khỏi phép so sánh).

| Model | n | Citation Acc | Faithfulness | Hallucination | Refusal Acc | p95 latency (ms) | Avg cost/req | Non-primary rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite (cheap) | 10 | 0.75 | 0.9375 | 0.125 | 1.0 | 1575 | 0.000906 | 0.0 |
| gemini-3-flash-preview (strong) | 10 | 0.75 | 1.0 | 0.0 | 1.0 | 16010 | 0.004526 | 0.0 |
| qwen2.5:7b (Ollama, local) | 10 | 0.5 | 0.667 | 0.5 | 0.8 | 32832 | 0.0 | 0.0 |

> **Ghi chú thật về `gemini-3-flash-preview`**: lần chạy đầu tiên (cùng
> `tier="strong"` như 2 model kia) bị fallback 10/10 sang `secondary`
> (thực chất là gọi `gemini-3.1-flash-lite` qua key khác — không phải
> model đang muốn đo) — xác nhận bằng 1 lệnh gọi cô lập ngay sau đó, vẫn
> fallback, không phải nhiễu tạm thời. Root cause thật: `tier="judge"`
> (dùng cho MỌI câu judge suốt session, kể cả 10 câu tier=cheap ở trên) và
> `tier="strong"` CÙNG dùng `gemini-3-flash-preview` qua CÙNG API key
> (primary) — 10 lệnh judge trước đó đã dùng gần hết quota key đó. Đã sửa
> bằng cách gọi thẳng route `strong-tertiary` (`config/litellm_config.yaml`,
> cùng model `gemini-3-flash-preview`, key khác — xác nhận qua header thật
> `x-litellm-model-api-base: .../gemini-3-flash-preview:generateContent`),
> bỏ qua chuỗi fallback tự động của tier `strong`. Đây là dữ liệu thật của
> ĐÚNG model `gemini-3-flash-preview`, chỉ khác đường gọi.

## Kết luận

- **gemini-3.1-flash-lite thắng rõ về cost-latency-quality trade-off** cho
  QA thường: citation_accuracy ngang `gemini-3-flash-preview` (0.75 cả
  hai, n=10 nên chênh lệch nhỏ chưa có ý nghĩa thống kê) nhưng rẻ hơn
  **~5 lần** ($0.0009 vs $0.0045/câu) và nhanh hơn **~10 lần** (p95 1.6s
  vs 16s) — đúng lý do dự án chọn flash-lite làm primary cho cả tier
  cheap/balanced (Phase 5-7), số liệu này xác nhận lại quyết định đó bằng
  đo thật thay vì chỉ dựa vào tốc độ quan sát được.
- **gemini-3-flash-preview chất lượng nhỉnh hơn thật** (hallucination
  0.0 vs 0.125, faithfulness 1.0 vs 0.9375) — hợp lý cho vai trò judge/
  strong-tier hiện tại (câu cần suy luận kỹ), nhưng chi phí+độ trễ quá
  lớn để dùng làm model mặc định cho traffic QA thường.
- **qwen2.5:7b (Ollama) kém nhất trên mọi trục** (citation_accuracy 0.5,
  faithfulness 0.667, hallucination 0.5, refusal_accuracy 0.8, VÀ chậm
  nhất — 32.8s p95, chậm hơn cả flash-preview) dù cost=0 — xác nhận lại
  bằng số liệu có kiểm soát (cùng 10 câu, cùng retrieval, cùng prompt)
  phát hiện đã biết từ Phase 8 (fallback thật xuống Ollama có
  refusal_accuracy thấp hẳn): model local là lưới an toàn cho reliability
  (không bao giờ downtime hoàn toàn), KHÔNG phải lựa chọn chất lượng
  tương đương — đúng thiết kế fallback hiện tại (chỉ dùng khi cả 3 hop
  Gemini đều lỗi).