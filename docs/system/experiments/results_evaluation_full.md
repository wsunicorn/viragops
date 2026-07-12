# Eval report — mode=full

> Sinh bởi `scripts/run_evaluation.py` lúc 20260712_1339 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p6_citation_complete_v1`. Số câu chạy: 298. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (252 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.934 | 0.850 | ĐẠT |
| Hit rate | 0.948 | | |
| MRR | 0.781 | | |
| Context Precision | 0.200 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.934 | 0.800 | ĐẠT |
| Context Relevance (judge) | 0.980 | 0.800 | ĐẠT |
| Faithfulness (judge) | 0.944 | 0.850 | ĐẠT |
| Answer Relevance (judge) | 0.962 | 0.800 | ĐẠT |
| Citation Accuracy | 0.781 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 0.950 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | 0.079 | 0.050 | CHƯA ĐẠT |
| p50 latency (generation) | 3759 ms | | |
| p95 latency (generation) | 6595 | 6000 | CHƯA ĐẠT |
| Avg cost/req | $0.000874 | <= $0.005 | ĐẠT |
| Error rate | 0.993 | <= 0.01 | CHƯA ĐẠT |
| Fallback rate | 0.993 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **⚠️ 296/298 câu (99.3%) bị phục vụ bởi fallback hop (không phải model primary)** — thường do quota/rate-limit cạn giữa run dài. Số liệu tổng hợp phía trên gồm cả các câu này; bảng dưới tách riêng để không đọc nhầm nhiễu hạ tầng thành gap chất lượng retrieval/prompt:

| Nhóm | n | Recall@k | Citation Acc | Refusal Acc | Faithfulness | p95 latency |
|---|---:|---:|---:|---:|---:|---:|
| primary | 2 | 0.500 | 0.500 | 1.000 | 0.750 | 1314 ms |
| fallback | 296 | 0.938 | 0.783 | 0.949 | 0.946 | 6595 ms |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|
| adversarial | 11 | n/a | 0.636 | n/a | 0.500 | 1.000 | 0.750 |
| ambiguous | 20 | 0.789 | 0.950 | 0.546 | 0.921 | 0.816 | 0.158 |
| factoid | 216 | 0.963 | 0.954 | 0.823 | 0.965 | 0.976 | 0.043 |
| multi_hop | 30 | 0.856 | 1.000 | 0.678 | 0.900 | 0.950 | 0.133 |
| out_of_scope | 9 | n/a | 1.000 | n/a | n/a | n/a | n/a |
| procedural | 12 | 0.917 | 1.000 | 0.750 | 0.917 | 1.000 | 0.167 |

## Failure cases (30 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_003 | factoid | Trong mỗi học kỳ chính, sinh viên IUH phải đăng ký tối thiểu và tối đa bao nhiêu | trace_error:served_by_fallback:tertiary |
| q_004 | factoid | Chương trình đào tạo trình độ đại học chính quy tại IUH có thời gian đào tạo chí | trace_error:served_by_fallback:tertiary |
| q_005 | procedural | Sinh viên IUH tích lũy được 80 tín chỉ thì được xếp vào trình độ năm đào tạo thứ | trace_error:served_by_fallback:tertiary |
| q_006 | factoid | Sinh viên IUH đã đăng ký và đóng học phí một học phần nhưng không đi học thì bị  | trace_error:served_by_fallback:tertiary |
| q_007 | factoid | Nếu sinh viên IUH không đóng học phí đúng thời hạn quy định sau khi đăng ký học  | trace_error:served_by_fallback:tertiary |
| q_008 | factoid | Sinh viên IUH có học phần bắt buộc bị điểm F thì phải làm gì? | trace_error:served_by_fallback:tertiary |
| q_009 | factoid | Sinh viên IUH đạt các mức điểm chữ nào thì được phép đăng ký học cải thiện điểm? | trace_error:served_by_fallback:tertiary |
| q_010 | factoid | Công thức tính điểm tổng kết học phần lý thuyết tại IUH là gì? | trace_error:served_by_fallback:tertiary |
| q_011 | factoid | Điểm thi kết thúc học phần tại IUH tối thiểu phải đạt bao nhiêu để không bị tính | trace_error:served_by_fallback:tertiary |
| q_012 | factoid | Sinh viên IUH có điểm thi giữa kỳ bằng 0 thì có được dự thi kết thúc học phần kh | trace_error:served_by_fallback:tertiary |
| q_013 | procedural | Sinh viên IUH đạt điểm 8.7 trên thang điểm 10 cho một học phần thì được quy đổi  | trace_error:served_by_fallback:tertiary |
| q_014 | factoid | Bài thi tự luận, tiểu luận kết thúc học phần tại IUH do bao nhiêu cán bộ chấm th | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_015 | factoid | Đề thi chính thức tại IUH phải được bàn giao cho Phòng Khảo thí và Đảm bảo Chất  | faithfulness=0.5; hallucination; trace_error:served_by_fallback:tertiary |
| q_070 | factoid | Phòng Khảo thí và Đảm bảo Chất lượng của IUH lưu trữ đầu phách bài thi kết thúc  | trace_error:served_by_fallback:tertiary |
| q_071 | factoid | Việc đánh phách bài thi kết thúc học phần tại IUH phải hoàn thành trong bao lâu  | trace_error:served_by_fallback:tertiary |
| q_072 | factoid | Bài thi tự luận kết thúc học phần tại IUH được chấm theo quy trình mấy vòng độc  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_073 | factoid | Khi hai cán bộ chấm thi tự luận tại IUH không thống nhất được điểm, quy trình xử | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_074 | factoid | Tổng thời gian trình bày và trả lời câu hỏi của một sinh viên khi thi vấn đáp tạ | trace_error:served_by_fallback:tertiary |
| q_075 | factoid | Khi chấm tiểu luận, đồ án cuối kỳ tại IUH, nếu kết quả chấm giữa 2 giảng viên ch | trace_error:served_by_fallback:tertiary |
| q_016 | factoid | Sinh viên IUH có bao nhiêu ngày kể từ khi điểm thi được công bố để nộp đơn phúc  | citation_sai (0.50); faithfulness=0.5; hallucination; trace_error:served_by_fallback:tertiary |
| q_017 | factoid | Việc chấm phúc khảo bài thi tự luận tại IUH phải hoàn thành trong bao lâu kể từ  | trace_error:served_by_fallback:tertiary |
| q_018 | factoid | Đơn vị chủ quản môn học phần phải thông báo kết quả phúc khảo tới sinh viên tron | trace_error:served_by_fallback:tertiary |
| q_019 | factoid | Hình thức thi nào tại IUH không được chấm phúc khảo? | trace_error:served_by_fallback:tertiary |
| q_020 | factoid | Quy định phúc khảo hiện hành của IUH được trích từ Điều nào, thuộc Quyết định số | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_022 | factoid | Điểm trung bình tích lũy tối thiểu để sinh viên IUH được xét và công nhận tốt ng | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_023 | factoid | Sinh viên đại học chính quy và tăng cường tiếng Anh, khóa tuyển sinh từ 2021 trở | trace_error:served_by_fallback:tertiary |
| q_024 | factoid | Sinh viên hệ vừa làm vừa học, đại học liên thông khóa tuyển sinh từ 2021 trở về  | citation_sai (0.33); trace_error:served_by_fallback:tertiary |
| q_025 | factoid | Sinh viên đại học chính quy khóa tuyển sinh 2018 cần đạt điểm TOEIC tối thiểu ba | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_026 | factoid | Sinh viên IUH được Nhà trường cử đi nước ngoài làm thực tập sinh liên tục từ bao | citation_sai (0.00); trace_error:served_by_fallback:tertiary |