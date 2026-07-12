// Real engineering findings from this project's build log (CHECKLIST_
// IMPLEMENTATION.md "Chưa tốt" sections + git history) — the honest,
// specific incidents, not marketing bullet points.

export type Finding = {
  title: string;
  tag: string;
  story: string;
  evidence: string;
};

export const FINDINGS: Finding[] = [
  {
    tag: "Data quality",
    title: "Golden set tự tìm ra lỗi trong chính nó",
    story:
      "Khi điều tra vì sao Citation Accuracy thấp ở câu multi-hop, phát hiện 6 câu hỏi trích dẫn nhầm nguồn (trang tóm tắt thay vì văn bản gốc) — và q_021's ground_truth SAI thật (\"Trưởng bộ môn\" thay vì đúng là \"GV giảng dạy\"). Model đã trả lời đúng hơn cả đáp án chuẩn.",
    evidence: "Xác nhận qua đối chiếu trace thật + văn bản Điều 26 Khoản 2.b QĐ 610",
  },
  {
    tag: "Vận hành thật",
    title: "3 lần cạn quota trong 1 ngày",
    story:
      "Chạy full eval + Phase 4 re-run liên tiếp trong cùng ngày làm cạn quota Gemini free-tier 3 lần liên tiếp — mỗi lần user cấp thêm 1 API key mới. LiteLLM gateway giờ có 4 chặng fallback: 3 key Gemini rồi mới tới Ollama local.",
    evidence: "config/litellm_config.yaml — cheap/balanced/strong/judge × primary/secondary/tertiary/local",
  },
  {
    tag: "Tự phát hiện hồi quy",
    title: "Sửa 1 lỗi, gây ra 1 lỗi khác — rồi tự bắt được",
    story:
      "Sửa prompt để tăng Citation Accuracy (p6) vô tình làm giảm Refusal Accuracy nhóm adversarial từ 0.909 xuống 0.636 — model vẫn từ chối đúng bản chất nhưng quên gắn cờ refusal vì tìm được đoạn để giải thích. Full eval 300 câu bắt được ngay, sửa tiếp bằng p7, verify sạch 11/11.",
    evidence: "results_prompt_comparison_p6.md → CHECKLIST Phase 8 mục 4",
  },
  {
    tag: "Kết quả âm tính",
    title: "Một thí nghiệm 'thất bại' vẫn đáng công bố",
    story:
      "Thử tăng số chunk đưa cho model (top_k_after 5→10) để vớt thêm citation cho câu multi-hop. Retrieval-only cho thấy tốt hơn ở mọi category — nhưng đo qua generation thật thì Citation Accuracy lại GIẢM. Đã revert, ghi lại làm bài học thay vì giấu đi.",
    evidence: "results_context_limit_ablation.md",
  },
];
