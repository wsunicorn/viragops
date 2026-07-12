# Eval report — mode=targeted

> Sinh bởi `scripts/run_evaluation.py` lúc 20260712_1349 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p7_citation_complete_safe_v1`. Số câu chạy: 30. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (0 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@10 | 0.889 | 0.850 | ĐẠT |
| Hit rate | 0.967 | | |
| MRR | 0.671 | | |
| Context Precision | 0.137 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.889 | 0.800 | ĐẠT |
| Context Relevance (judge) | n/a | 0.800 |  |
| Faithfulness (judge) | n/a | 0.850 |  |
| Answer Relevance (judge) | n/a | 0.800 |  |
| Citation Accuracy | 0.650 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 1.000 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | n/a | 0.050 |  |
| p50 latency (generation) | 4051 ms | | |
| p95 latency (generation) | 5559 | 6000 | ĐẠT |
| Avg cost/req | $0.001533 | <= $0.005 | ĐẠT |
| Error rate | 1.000 | <= 0.01 | CHƯA ĐẠT |
| Fallback rate | 1.000 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_hop | 30 | 0.889 | 1.000 | 0.650 | n/a | n/a | n/a |

## Failure cases (30 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_028 | multi_hop | Sinh viên đạt điểm trung bình tích lũy ở mức xếp hạng Giỏi nhưng từng bị kỷ luật | trace_error:served_by_fallback:tertiary |
| q_069 | multi_hop | Nếu một sinh viên IUH vừa bị xếp loại rèn luyện Kém hai học kỳ liên tiếp, vừa từ | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_056 | multi_hop | Sinh viên IUH bị cảnh báo kết quả học tập dựa trên những điều kiện nào, và bị bu | trace_error:served_by_fallback:tertiary |
| q_128 | multi_hop | Sinh viên IUH có điểm thi giữa kỳ bằng 0 thì có được dự thi kết thúc học phần kh | trace_error:served_by_fallback:tertiary |
| q_129 | multi_hop | Sinh viên IUH bị buộc thôi học do vượt quá thời gian đào tạo tối đa thì có được  | citation_sai (0.33); trace_error:served_by_fallback:tertiary |
| q_130 | multi_hop | Sinh viên IUH nộp đơn phúc khảo bài thi tự luận thì quy trình xử lý và thời hạn  | citation_sai (0.33); trace_error:served_by_fallback:tertiary |
| q_131 | multi_hop | Sinh viên IUH muốn học chương trình thứ hai thì cần đáp ứng điều kiện gì về học  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_132 | multi_hop | Sinh viên IUH bị điểm F ở một học phần bắt buộc, sau đó đăng ký học lại và tiếp  | trace_error:served_by_fallback:tertiary |
| q_133 | multi_hop | Sinh viên IUH được xét học bổng Khuyến khích học tập cần tích lũy tối thiểu bao  | citation_sai (0.67); trace_error:served_by_fallback:tertiary |
| q_179 | multi_hop | Sinh viên IUH nghỉ học tạm thời vì lý do cá nhân và đã dùng hết 2 lần cho phép,  | trace_error:served_by_fallback:tertiary |
| q_180 | multi_hop | Sinh viên IUH học chương trình tăng cường tiếng Anh muốn chuyển sang chương trìn | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_181 | multi_hop | Sinh viên IUH bị cấm thi kết thúc học phần vì điểm giữa kỳ bằng 0, sau đó phải đ | trace_error:served_by_fallback:tertiary |
| q_182 | multi_hop | Sinh viên IUH nộp đơn phúc khảo bài thi tự luận và kết quả phúc khảo cho thấy đi | trace_error:served_by_fallback:tertiary |
| q_183 | multi_hop | Sinh viên IUH bị xếp loại rèn luyện Kém trong học kỳ xét học bổng thì có đủ điều | retrieval_miss (hit@k=0); citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_184 | multi_hop | Sinh viên IUH đăng ký học phần bắt buộc bị áp cứng nhưng muốn hủy để đăng ký học | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_185 | multi_hop | Sinh viên IUH là người dân tộc thiểu số hộ nghèo vừa được miễn 100% học phí, vừa | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_225 | multi_hop | Sinh viên IUH đăng ký học phần mở rộng ngoài chương trình đào tạo của ngành thì  | trace_error:served_by_fallback:tertiary |
| q_226 | multi_hop | Sinh viên IUH thi trực tuyến hình thức trắc nghiệm bị phát hiện gian lận (ví dụ  | trace_error:served_by_fallback:tertiary |
| q_227 | multi_hop | Sinh viên IUH học chương trình thứ hai mà bị buộc thôi học ở chương trình thứ nh | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_228 | multi_hop | Sinh viên IUH nộp đơn xin nghỉ học tạm thời vì lý do cá nhân sau khi học kỳ đó đ | trace_error:served_by_fallback:tertiary |
| q_229 | multi_hop | Sinh viên IUH đăng ký học cải thiện điểm cho một học phần đã đạt điểm B, sau đó  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_230 | multi_hop | Sinh viên IUH đang trong thời gian bị đình chỉ học tập 1 năm do kỷ luật thi hộ,  | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_231 | multi_hop | So sánh thời hạn phúc khảo điểm thi trắc nghiệm và bài thi kết thúc học phần nói | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_232 | multi_hop | Sinh viên IUH được xếp hạng tốt nghiệp loại Giỏi nhưng khối lượng học phần phải  | trace_error:served_by_fallback:tertiary |
| q_254 | multi_hop | Sinh viên IUH bị cấm thi kết thúc học phần vì vắng quá 50% số bài kiểm tra thườn | trace_error:served_by_fallback:tertiary |
| q_255 | multi_hop | Sinh viên IUH đăng ký chương trình thứ hai và học phần trùng nội dung với chương | citation_sai (0.67); trace_error:served_by_fallback:tertiary |
| q_256 | multi_hop | Sinh viên IUH học liên thông từ cao đẳng lên đại học được công nhận kết quả các  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_257 | multi_hop | Nếu một cán bộ coi thi tại IUH để sinh viên tự do quay cóp mà bị cán bộ giám sát | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_258 | multi_hop | Sinh viên IUH đủ điều kiện tốt nghiệp nhưng chưa hoàn thành chứng chỉ Giáo dục Q | citation_sai (0.50); trace_error:served_by_fallback:tertiary |