# Eval report — mode=targeted

> Sinh bởi `scripts/run_evaluation.py` lúc 20260714_0410 UTC. data_version=`data_20260713`, index_version=`idx_20260713_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p7_citation_complete_safe_v1`. Số câu chạy: 30. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (29 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.856 | 0.850 | ĐẠT |
| Hit rate | 0.967 | | |
| MRR | 0.668 | | |
| Context Precision | 0.260 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.856 | 0.800 | ĐẠT |
| Context Relevance (judge) | 0.983 | 0.800 | ĐẠT |
| Faithfulness (judge) | 0.862 | 0.850 | ĐẠT |
| Answer Relevance (judge) | 0.914 | 0.800 | ĐẠT |
| Citation Accuracy | 0.684 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 0.967 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | 0.276 | 0.050 | CHƯA ĐẠT |
| p50 latency (generation) | 1356 ms | | |
| p95 latency (generation) | 1711 | 6000 | ĐẠT |
| Avg cost/req | $0.001001 | <= $0.005 | ĐẠT |
| Error rate | 0.000 | <= 0.01 | ĐẠT |
| Fallback rate | 0.000 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination | Ambiguity handled |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| multi_hop | 30 | 0.856 | 0.967 | 0.684 | 0.862 | 0.914 | 0.276 | - |

> **Ambiguity handled** (chỉ category `ambiguous`, requires_clarification=True): % câu trả lời hoặc hỏi lại người dùng để làm rõ, hoặc bao quát đủ các nhánh điều kiện thay vì chốt 1 nhánh duy nhất — đo bằng heuristic văn bản (`src/evaluation/metrics.py::ambiguity_handled`), không tốn thêm lệnh gọi judge. Hệ thống hiện KHÔNG có prompt/cơ chế hỏi lại làm rõ (xem src/promptops/templates.py) nên `refusal_accuracy` luôn 'đúng' một cách vô nghĩa cho category này (requires_refusal=False, hệ thống không refuse) — cột này là chỉ số thật duy nhất phản ánh có xử lý mơ hồ hợp lý hay không.

## Failure cases (18 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_021 | multi_hop | Nếu chấm phúc khảo phát hiện sai lệch điểm, ai chịu trách nhiệm chuyển hồ sơ và  | citation_sai (0.33); faithfulness=0.5; hallucination |
| q_069 | multi_hop | Nếu một sinh viên IUH vừa bị xếp loại rèn luyện Kém hai học kỳ liên tiếp, vừa từ | citation_sai (0.00) |
| q_129 | multi_hop | Sinh viên IUH bị buộc thôi học do vượt quá thời gian đào tạo tối đa thì có được  | citation_sai (0.50) |
| q_130 | multi_hop | Sinh viên IUH nộp đơn phúc khảo bài thi tự luận thì quy trình xử lý và thời hạn  | citation_sai (0.50) |
| q_132 | multi_hop | Sinh viên IUH bị điểm F ở một học phần bắt buộc, sau đó đăng ký học lại và tiếp  | citation_sai (0.67) |
| q_133 | multi_hop | Sinh viên IUH được xét học bổng Khuyến khích học tập cần tích lũy tối thiểu bao  | citation_sai (0.67) |
| q_180 | multi_hop | Sinh viên IUH học chương trình tăng cường tiếng Anh muốn chuyển sang chương trìn | citation_sai (0.00) |
| q_183 | multi_hop | Sinh viên IUH bị xếp loại rèn luyện Kém trong học kỳ xét học bổng thì có đủ điều | retrieval_miss (hit@k=0); citation_sai (0.00) |
| q_184 | multi_hop | Sinh viên IUH đăng ký học phần bắt buộc bị áp cứng nhưng muốn hủy để đăng ký học | citation_sai (0.50) |
| q_185 | multi_hop | Sinh viên IUH là người dân tộc thiểu số hộ nghèo vừa được miễn 100% học phí, vừa | citation_sai (0.00); faithfulness=0.5; hallucination |
| q_226 | multi_hop | Sinh viên IUH thi trực tuyến hình thức trắc nghiệm bị phát hiện gian lận (ví dụ  | faithfulness=0.5; hallucination |
| q_227 | multi_hop | Sinh viên IUH học chương trình thứ hai mà bị buộc thôi học ở chương trình thứ nh | citation_sai (0.50); faithfulness=0.5; hallucination |
| q_228 | multi_hop | Sinh viên IUH nộp đơn xin nghỉ học tạm thời vì lý do cá nhân sau khi học kỳ đó đ | faithfulness=0.5; hallucination |
| q_229 | multi_hop | Sinh viên IUH đăng ký học cải thiện điểm cho một học phần đã đạt điểm B, sau đó  | refusal_sai (kỳ vọng refusal=False, thực tế=True) |
| q_230 | multi_hop | Sinh viên IUH đang trong thời gian bị đình chỉ học tập 1 năm do kỷ luật thi hộ,  | citation_sai (0.00); faithfulness=0.5; hallucination |
| q_231 | multi_hop | So sánh thời hạn phúc khảo điểm thi trắc nghiệm và bài thi kết thúc học phần nói | citation_sai (0.50) |
| q_256 | multi_hop | Sinh viên IUH học liên thông từ cao đẳng lên đại học được công nhận kết quả các  | faithfulness=0.5; hallucination |
| q_257 | multi_hop | Nếu một cán bộ coi thi tại IUH để sinh viên tự do quay cóp mà bị cán bộ giám sát | citation_sai (0.67); faithfulness=0.5; hallucination |