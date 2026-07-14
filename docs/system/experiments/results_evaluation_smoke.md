# Eval report — mode=smoke

> Sinh bởi `scripts/run_evaluation.py` lúc 20260714_0320 UTC. data_version=`data_20260713`, index_version=`idx_20260713_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p7_citation_complete_safe_v1`. Số câu chạy: 50. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (40 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.905 | 0.850 | ĐẠT |
| Hit rate | 0.919 | | |
| MRR | 0.824 | | |
| Context Precision | 0.189 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.905 | 0.800 | ĐẠT |
| Context Relevance (judge) | 0.988 | 0.800 | ĐẠT |
| Faithfulness (judge) | 0.950 | 0.850 | ĐẠT |
| Answer Relevance (judge) | 0.963 | 0.800 | ĐẠT |
| Citation Accuracy | 0.838 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 0.900 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | 0.100 | 0.050 | CHƯA ĐẠT |
| p50 latency (generation) | 796 ms | | |
| p95 latency (generation) | 1287 | 6000 | ĐẠT |
| Avg cost/req | $0.000918 | <= $0.005 | ĐẠT |
| Error rate | 0.000 | <= 0.01 | ĐẠT |
| Fallback rate | 0.000 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination | Ambiguity handled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| adversarial | 2 | n/a | 1.000 | n/a | n/a | n/a | n/a | - |
| ambiguous | 3 | 0.667 | 1.000 | 0.667 | 1.000 | 0.833 | 0.000 | 0.667 (3) |
| factoid | 36 | 0.926 | 0.861 | 0.878 | 0.983 | 1.000 | 0.033 | - |
| multi_hop | 5 | 0.900 | 1.000 | 0.667 | 0.800 | 0.800 | 0.400 | - |
| out_of_scope | 2 | n/a | 1.000 | n/a | n/a | n/a | n/a | - |
| procedural | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.500 | - |

> **Ambiguity handled** (chỉ category `ambiguous`, requires_clarification=True): % câu trả lời hoặc hỏi lại người dùng để làm rõ, hoặc bao quát đủ các nhánh điều kiện thay vì chốt 1 nhánh duy nhất — đo bằng heuristic văn bản (`src/evaluation/metrics.py::ambiguity_handled`), không tốn thêm lệnh gọi judge. Hệ thống hiện KHÔNG có prompt/cơ chế hỏi lại làm rõ (xem src/promptops/templates.py) nên `refusal_accuracy` luôn 'đúng' một cách vô nghĩa cho category này (requires_refusal=False, hệ thống không refuse) — cột này là chỉ số thật duy nhất phản ánh có xử lý mơ hồ hợp lý hay không.

## Failure cases (16 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.50); faithfulness=0.5; hallucination |
| q_049 | factoid | Học phí một tín chỉ ngành Công nghệ Thông tin hệ đại trà năm học 2026-2027 tại I | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_055 | ambiguous | Em bị rớt môn thì phải làm sao? | ambiguity_unhandled (chốt 1 nhánh, không hỏi lại/bao quát) |
| q_058 | factoid | Mức kỷ luật Cảnh cáo tại IUH được áp dụng trong trường hợp nào? | citation_sai (0.50) |
| q_130 | multi_hop | Sinh viên IUH nộp đơn phúc khảo bài thi tự luận thì quy trình xử lý và thời hạn  | citation_sai (0.33) |
| q_184 | multi_hop | Sinh viên IUH đăng ký học phần bắt buộc bị áp cứng nhưng muốn hủy để đăng ký học | citation_sai (0.50) |
| q_199 | ambiguous | Em muốn xin học bổng thì cần làm gì? | retrieval_miss (hit@k=0); citation_sai (0.00) |
| q_208 | factoid | Đại học liên thông từ trình độ cao đẳng tại IUH có thời gian đào tạo chính khóa  | citation_sai (0.00) |
| q_218 | factoid | Nội dung đề thi tại IUH phải đảm bảo các yêu cầu gì về mặt khoa học và bảo mật? | citation_sai (0.33) |
| q_226 | multi_hop | Sinh viên IUH thi trực tuyến hình thức trắc nghiệm bị phát hiện gian lận (ví dụ  | faithfulness=0.5; hallucination |
| q_235 | factoid | Mức học phí học phần mở rộng (ngoài chương trình đào tạo) tại IUH năm học 2026-2 | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_236 | factoid | Kết quả đánh giá kiểm định chất lượng giáo dục cấp cơ sở giáo dục của IUH chu kỳ | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_264 | factoid | Danh sách các trường THPT chuyên được công nhận để xét học bổng tuyển sinh tại I | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_287 | factoid | Trong trường hợp thiên tai, dịch bệnh phức tạp, việc tổ chức thi giữa kỳ và cuối | retrieval_miss (hit@k=0); citation_sai (0.00); faithfulness=0.5; hallucination |
| q_293 | procedural | Trong quy trình phúc khảo điểm tại IUH, hồ sơ (đơn và biên lai) sau khi giáo vụ  | faithfulness=0.5; hallucination |
| q_300 | factoid | Sinh viên IUH tốt nghiệp sớm hơn thời gian đào tạo tối thiểu quy định có được Nh | refusal_sai (kỳ vọng refusal=False, thực tế=True); retrieval_miss (hit@k=0) |