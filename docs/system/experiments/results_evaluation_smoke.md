# Eval report — mode=smoke

> Sinh bởi `scripts/run_evaluation.py` lúc 20260712_0756 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p1_grounded_v1`. Số câu chạy: 50. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (37 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.905 | 0.850 | ĐẠT |
| Hit rate | 0.919 | | |
| MRR | 0.813 | | |
| Context Precision | 0.189 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.905 | 0.800 | ĐẠT |
| Context Relevance (judge) | 0.973 | 0.800 | ĐẠT |
| Faithfulness (judge) | 0.973 | 0.850 | ĐẠT |
| Answer Relevance (judge) | 0.973 | 0.800 | ĐẠT |
| Citation Accuracy | 0.838 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 0.880 | 0.900 | CHƯA ĐẠT |
| Hallucination Rate (judge) | 0.027 | 0.050 | ĐẠT |
| p50 latency (generation) | 1147 ms | | |
| p95 latency (generation) | 1397 | 6000 | ĐẠT |
| Avg cost/req | $0.000746 | <= $0.005 | ĐẠT |
| Error rate | 0.020 | <= 0.01 | CHƯA ĐẠT |
| Fallback rate | 0.000 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|
| adversarial | 2 | n/a | 1.000 | n/a | n/a | n/a | n/a |
| ambiguous | 3 | 0.667 | 0.667 | 1.000 | 1.000 | 0.750 | 0.000 |
| factoid | 36 | 0.926 | 0.889 | 0.878 | 0.983 | 0.983 | 0.000 |
| multi_hop | 5 | 0.900 | 0.800 | 0.417 | 1.000 | 1.000 | 0.000 |
| out_of_scope | 2 | n/a | 1.000 | n/a | n/a | n/a | n/a |
| procedural | 2 | 1.000 | 1.000 | 1.000 | 0.750 | 1.000 | 0.500 |

## Failure cases (14 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.00) |
| q_032 | factoid | Sinh viên trình độ năm thứ hai tại IUH bị cảnh báo kết quả học tập nếu điểm trun | citation_sai (0.50) |
| q_130 | multi_hop | Sinh viên IUH nộp đơn phúc khảo bài thi tự luận thì quy trình xử lý và thời hạn  | citation_sai (0.33) |
| q_184 | multi_hop | Sinh viên IUH đăng ký học phần bắt buộc bị áp cứng nhưng muốn hủy để đăng ký học | citation_sai (0.33) |
| q_199 | ambiguous | Em muốn xin học bổng thì cần làm gì? | refusal_sai (kỳ vọng refusal=False, thực tế=True); retrieval_miss (hit@k=0); trace_error:unparseable_model_output |
| q_208 | factoid | Đại học liên thông từ trình độ cao đẳng tại IUH có thời gian đào tạo chính khóa  | citation_sai (0.00) |
| q_218 | factoid | Nội dung đề thi tại IUH phải đảm bảo các yêu cầu gì về mặt khoa học và bảo mật? | citation_sai (0.33) |
| q_235 | factoid | Mức học phí học phần mở rộng (ngoài chương trình đào tạo) tại IUH năm học 2026-2 | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_236 | factoid | Kết quả đánh giá kiểm định chất lượng giáo dục cấp cơ sở giáo dục của IUH chu kỳ | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_254 | multi_hop | Sinh viên IUH bị cấm thi kết thúc học phần vì vắng quá 50% số bài kiểm tra thườn | refusal_sai (kỳ vọng refusal=False, thực tế=True) |
| q_264 | factoid | Danh sách các trường THPT chuyên được công nhận để xét học bổng tuyển sinh tại I | refusal_sai (kỳ vọng refusal=True, thực tế=False) |
| q_287 | factoid | Trong trường hợp thiên tai, dịch bệnh phức tạp, việc tổ chức thi giữa kỳ và cuối | retrieval_miss (hit@k=0); citation_sai (0.00); faithfulness=0.5 |
| q_293 | procedural | Trong quy trình phúc khảo điểm tại IUH, hồ sơ (đơn và biên lai) sau khi giáo vụ  | faithfulness=0.5; hallucination |
| q_300 | factoid | Sinh viên IUH tốt nghiệp sớm hơn thời gian đào tạo tối thiểu quy định có được Nh | refusal_sai (kỳ vọng refusal=False, thực tế=True); retrieval_miss (hit@k=0) |
