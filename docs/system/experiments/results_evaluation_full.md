# Eval report — mode=full

> Sinh bởi `scripts/run_evaluation.py` lúc 20260712_0938 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p1_grounded_v1`. Số câu chạy: 298. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (225 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.931 | 0.850 | ĐẠT |
| Hit rate | 0.943 | | |
| MRR | 0.794 | | |
| Context Precision | 0.198 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.931 | 0.800 | ĐẠT |
| Context Relevance (judge) | 0.987 | 0.800 | ĐẠT |
| Faithfulness (judge) | 0.967 | 0.850 | ĐẠT |
| Answer Relevance (judge) | 0.960 | 0.800 | ĐẠT |
| Citation Accuracy | 0.785 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 0.903 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | 0.058 | 0.050 | CHƯA ĐẠT |
| p50 latency (generation) | 1143 ms | | |
| p95 latency (generation) | 16737 | 6000 | CHƯA ĐẠT |
| Avg cost/req | $0.000915 | <= $0.005 | ĐẠT |
| Error rate | 0.117 | <= 0.01 | CHƯA ĐẠT |
| Fallback rate | 0.117 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **⚠️ Phát hiện quan trọng — 35/298 câu (11.7%) bị phục vụ bởi fallback hop, tập trung ở đuôi run (khoảng q_272-q_300):** cả 2 key Gemini (primary + secondary) cạn quota/rate-limit gần cuối lần chạy 54 phút liên tục này (dùng chung ngân sách ngày với smoke eval + Phase 4 chạy trước đó cùng ngày) — LiteLLM proxy tự động rơi xuống **Ollama local (qwen2.5:7b)** cho 19 câu cuối theo đúng thiết kế fallback Phase 7. Vấn đề: Ollama local hay trả JSON có citation không hợp lệ (`answer_without_valid_citation`/`invalid_citations_dropped`) → bị `citation.py` tự động hạ thành refusal (đúng chính sách fail-closed) → làm SAI LỆCH số liệu tổng hợp phía trên (đặc biệt Refusal Accuracy, latency). Bóc tách theo `fallback_hop` (tính lại thủ công từ CSV) cho bức tranh chính xác hơn:
>
> | Nhóm | n | Recall@5 | Citation Acc | Refusal Acc | Faithfulness | p50/p95 latency |
> |---|---:|---:|---:|---:|---:|---:|
> | **primary (sạch)** | 263 | 0.940 | 0.781 | **0.962** | 0.967 | 1123 / 1490 ms |
> | fallback (secondary+local) | 35 | 0.867 | 0.864* | **0.457** | 0.955 | 15672 / 23699 ms |
>
> *(citation accuracy fallback cao hơn do survivorship bias — nhiều câu fallback bị hạ refusal nên loại khỏi mẫu tính, không phải bằng chứng Ollama trích dẫn tốt hơn.)*
>
> **Kết luận đúng của lần chạy này:** trên đường primary (88% số câu, phản ánh đúng chất lượng retrieval/prompt/model thật), **Refusal Accuracy = 0.962 — VƯỢT target 0.90** (tốt hơn cả số đo được ở smoke 50 câu là 0.880) và **p95 latency = 1.49s — ĐẠT target 6s thoải mái**. Số liệu tổng hợp "CHƯA ĐẠT" ở Refusal Accuracy/p95 latency trong bảng trên là do nhiễu hạ tầng (quota cạn giữa chừng), không phải lỗi retrieval/prompt/model. **Citation Accuracy (0.781 trên đường sạch) là gap THẬT, không bị nhiễu** — nhất quán với smoke (0.838) và với phân tích theo category bên dưới (yếu nhất ở multi_hop/ambiguous). Bài học vận hành: eval quy mô 300 câu liên tục trong 1 phiên dễ cạn quota ngày nếu chạy sau khi đã dùng nhiều quota cho việc khác cùng ngày — nên chạy full eval vào đầu ngày hoặc tách nhiều phiên.

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|
| adversarial | 11 | n/a | 0.909 | n/a | 1.000 | 1.000 | 0.000 |
| ambiguous | 19 | 0.778 | 0.789 | 0.452 | 0.867 | 0.800 | 0.200 |
| factoid | 218 | 0.957 | 0.908 | 0.843 | 0.980 | 0.985 | 0.041 |
| multi_hop | 29 | 0.862 | 0.966 | 0.625 | 0.929 | 0.875 | 0.107 |
| out_of_scope | 9 | n/a | 1.000 | n/a | n/a | n/a | n/a |
| procedural | 12 | 0.917 | 0.750 | 0.722 | 1.000 | 1.000 | 0.000 |

## Failure cases (30 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_014 | factoid | Bài thi tự luận, tiểu luận kết thúc học phần tại IUH do bao nhiêu cán bộ chấm th | citation_sai (0.50) |
| q_016 | factoid | Sinh viên IUH có bao nhiêu ngày kể từ khi điểm thi được công bố để nộp đơn phúc  | citation_sai (0.33) |
| q_018 | factoid | Đơn vị chủ quản môn học phần phải thông báo kết quả phúc khảo tới sinh viên tron | citation_sai (0.00); faithfulness=0.5; hallucination |
| q_019 | factoid | Hình thức thi nào tại IUH không được chấm phúc khảo? | citation_sai (0.50) |
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.00); faithfulness=0.5; hallucination |
| q_022 | factoid | Điểm trung bình tích lũy tối thiểu để sinh viên IUH được xét và công nhận tốt ng | citation_sai (0.50) |
| q_024 | factoid | Sinh viên hệ vừa làm vừa học, đại học liên thông khóa tuyển sinh từ 2021 trở về  | citation_sai (0.33) |
| q_025 | factoid | Sinh viên đại học chính quy khóa tuyển sinh 2018 cần đạt điểm TOEIC tối thiểu ba | citation_sai (0.33) |
| q_026 | factoid | Sinh viên IUH được Nhà trường cử đi nước ngoài làm thực tập sinh liên tục từ bao | citation_sai (0.50) |
| q_032 | factoid | Sinh viên trình độ năm thứ hai tại IUH bị cảnh báo kết quả học tập nếu điểm trun | citation_sai (0.50) |
| q_033 | factoid | Sinh viên IUH bị cảnh báo kết quả học tập bao nhiêu lần liên tiếp thì bị xem xét | citation_sai (0.50) |
| q_034 | factoid | Sinh viên IUH tự ý bỏ học liên tục bao nhiêu học kỳ thì bị buộc thôi học? | citation_sai (0.50) |
| q_035 | factoid | Sinh viên IUH nhờ người khác thi hộ trong kỳ thi, vi phạm lần đầu tiên, bị xử lý | citation_sai (0.50) |
| q_036 | factoid | Nếu sinh viên IUH vi phạm thi hộ lần thứ hai thì bị xử lý kỷ luật ra sao? | citation_sai (0.25) |
| q_037 | factoid | Người học sử dụng văn bằng, chứng chỉ giả làm điều kiện xét tốt nghiệp tại IUH s | citation_sai (0.50) |
| q_058 | factoid | Mức kỷ luật Cảnh cáo tại IUH được áp dụng trong trường hợp nào? | citation_sai (0.50) |
| q_038 | factoid | Sinh viên IUH xin nghỉ học tạm thời vì nhu cầu cá nhân được Nhà trường giải quyế | citation_sai (0.50) |
| q_039 | factoid | Mỗi lần nghỉ học tạm thời vì nhu cầu cá nhân tại IUH được duyệt tối đa bao lâu? | citation_sai (0.50) |
| q_041 | factoid | Sinh viên IUH được xét chuyển ngành đào tạo tối đa bao nhiêu lần trong suốt khóa | citation_sai (0.50) |
| q_042 | procedural | Sinh viên năm thứ nhất tại IUH có được xin chuyển ngành theo nhu cầu cá nhân khô | citation_sai (0.50) |
| q_044 | factoid | Sinh viên IUH có điểm trung bình chung tích lũy 2.50 (thang điểm 4) ở chương trì | citation_sai (0.50) |
| q_045 | factoid | Sinh viên chương trình đại trà tại IUH phải đạt học phần Tiếng Anh nào trước khi | citation_sai (0.50) |
| q_046 | factoid | Chương trình tăng cường tiếng Anh tại IUH yêu cầu sinh viên hoàn thành bao nhiêu | citation_sai (0.00) |
| q_047 | factoid | Chứng chỉ IELTS 4.0 tương đương với bậc mấy trong Khung năng lực ngoại ngữ 6 bậc | citation_sai (0.00) |
| q_048 | factoid | IUH có chấp nhận chứng chỉ TOEFL iBT phiên bản Home Edition để xét chuẩn đầu ra  | citation_sai (0.50) |
| q_061 | factoid | Điều kiện tối thiểu về số tín chỉ tích lũy trong học kỳ để sinh viên IUH được xé | citation_sai (0.50) |
| q_062 | factoid | Học kỳ đầu và học kỳ cuối của khóa học tại IUH có được xét học bổng Khuyến khích | citation_sai (0.50) |
| q_064 | factoid | Sinh viên IUH là người dân tộc thiểu số (không thuộc nhóm rất ít người) cư trú t | citation_sai (0.50) |
| q_065 | factoid | Sinh viên IUH là con của cán bộ, công chức bị tai nạn lao động hoặc mắc bệnh ngh | citation_sai (0.00) |
| q_069 | multi_hop | Nếu một sinh viên IUH vừa bị xếp loại rèn luyện Kém hai học kỳ liên tiếp, vừa từ | citation_sai (0.00) |