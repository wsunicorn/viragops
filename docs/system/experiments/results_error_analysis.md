# Error Analysis — tổng hợp mẫu hình lỗi xuyên suốt các thực nghiệm (Phase 12)

Không phải 1 báo cáo mới đo lại — gom các phát hiện lỗi ĐÃ ĐO THẬT rải rác qua nhiều phase/report thành 1 bức tranh.

## 1. Citation completeness ở câu nhiều vế (multi_hop/ambiguous) — vấn đề dai dẳng nhất, chưa giải quyết triệt để

Xuất hiện lặp lại ở MỌI lớp đo:
- Phase 8 full eval (p1): citation_accuracy multi_hop=0.625, ambiguous=0.452 (mẫu nhỏ, không đáng tin hoàn toàn).
- Phase 8 "Sửa citation accuracy" (p6/p7): cải thiện rõ (multi_hop 0.672→0.700, ambiguous 0.451→0.535) nhưng chưa đạt target 0.85.
- CHECKLIST item 9: per-hop retrieval — THỬ VÀ THẤT BẠI (baseline single-query vẫn thắng: 0.856 vs 0.767/0.650 citation accuracy).
- Phase 11: self-check prompt (p8_citation_multipart_v1) — THỬ VÀ THẤT BẠI (0.838→0.775, TỆ HƠN).
- Phase 12 Exp5 (self-review): 15/25 mẫu review lệch nhãn đều do câu trả lời nhiều vế chỉ trích được 1 phần citation.

**2 hướng đã thử ở tầng khác nhau (retrieval, prompt) đều không đủ** — hướng còn lại, chưa thử: validate SỐ LƯỢNG citation tối thiểu theo số vế câu hỏi ở tầng `src/rag/citation.py` (post-hoc, sau khi model trả lời, không dựa vào model tự giác) — nếu phát hiện thiếu, hạ confidence hoặc force refusal một phần thay vì chấp nhận câu trả lời có citation không đủ.

## 2. Ollama fallback — quality gap thật, đã lượng hoá nhiều lần

- Phase 7: xác nhận cascade fallback hoạt động đúng cơ chế (không sập hệ thống).
- Phase 8 full eval: nhóm fallback (Ollama) refusal_accuracy chỉ 0.457 so với primary 0.962 — gap rất lớn.
- Phase 8 debug: model 7B tự rút gọn chunk_id dài thành hậu tố số — không phải lỗi context-window (đã test cả num_ctx 4096/8192), là hạn chế thật của model nhỏ khi chép nguyên văn chuỗi dài — fix bằng suffix-match có validate duy nhất.
- Phase 12 Exp3 (model comparison có kiểm soát, cùng 10 câu/cùng retrieval): xác nhận lại rõ ràng nhất — qwen2.5:7b kém nhất mọi trục (citation_accuracy 0.5, faithfulness 0.667, hallucination 0.5) VÀ chậm nhất (p95 32.8s, chậm hơn cả flash-preview).

**Kết luận nhất quán qua 3 phase**: Ollama fallback đúng vai trò reliability (không downtime hoàn toàn), KHÔNG đúng vai trò duy trì chất lượng — thiết kế hiện tại (chỉ dùng khi cả 3 hop Gemini lỗi) là đúng, không nên mở rộng vai trò của nó.

## 3. Context Precision — giới hạn cấu trúc của metric, không phải lỗi hệ thống

Lặp lại CHÍNH XÁC cùng 1 caveat ở mọi report dùng metric này (Phase 8, Phase 10, Phase 11, Phase 12 Exp6): mẫu số cố định = top_k_after (hiện=5), tử số bị chặn trên bởi tổng số chunk liên quan thật/câu (thường 1-3 với factoid) → target 0.75 KHÔNG khả thi cấu trúc với retrieval top-5 cố định + ground truth thưa. Số liệu context_precision quan sát được (~0.18-0.24 xuyên suốt mọi report) phản ánh đúng giới hạn này, không phải retrieval kém — Context Recall/Hit rate mới là 2 chỉ số phản ánh đúng recall/reachability.

## 4. "Đo trước khi đổi production default" — nguyên tắc được xác nhận đúng nhiều lần qua kết quả tiêu cực

Không phải lỗi mà là một pattern phương pháp luận lặp lại đáng ghi nhận: mọi thay đổi "trông có vẻ hợp lý về mặt thiết kế" đều được đo thật trước khi áp dụng, và nhiều lần kết quả đo NGƯỢC với trực giác thiết kế:
- `top_k_after` 5→10: retrieval-only tốt hơn, nhưng generation thật TỆ HƠN (nhiều chunk hơn = nhiều distractor hơn) — revert.
- Reranker Gemini listwise: có vẻ nên bật (cải thiện chất lượng ở mẫu lớn), nhưng latency thật quá lớn khi rate-limit — giữ tắt.
- Per-hop retrieval cho multi-hop: có vẻ đúng hướng, đo thật lại thua baseline — revert.
- p8 self-check prompt: có vẻ đúng hướng (thêm bước tự kiểm tra), đo thật lại TỆ HƠN — không activate.

Bài học tổng hợp cho báo cáo khóa luận: trong LLMOps, trực giác thiết kế về "cái gì sẽ cải thiện chất lượng" sai khá thường xuyên khi đối chiếu với đo lường thật — quy trình evaluation+gate không phải thủ tục hình thức, mà là cơ chế bắt lỗi trực giác sai một cách hệ thống.

## 5. Quota/rate-limit là ràng buộc vận hành thật, không phải chi tiết vặt

Xuất hiện xuyên suốt: Phase 2 (OCR), Phase 4 (embedding batch), Phase 8 (full eval fallback), Phase 11 (multiple sessions), Phase 12 Exp3 (judge và strong-tier tranh chấp cùng 1 key/model, phải phát hiện và định tuyến lại qua route khác). Đây là ràng buộc LLMOps thật của việc vận hành trên free-tier nhiều nhà cung cấp — đáng đưa vào chương "hạn chế và hướng phát triển" của báo cáo khóa luận: một hệ thống production thật cần budget/quota theo dõi được PER-MODEL (không chỉ per-key), điều dự án hiện chưa làm (chỉ có `daily_budget_usd` tổng, không tách theo model).
