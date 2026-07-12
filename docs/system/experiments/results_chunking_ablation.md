# Kết quả experiment: chunking_ablation

> Sinh bởi `scripts/run_experiment.py` lúc 20260712_0723 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, embedding=`gemini-embedding-001`. Metric tính ở k=5 theo `contracts/metric_definitions.md`; relevance = citation-coverage (xem docstring `src/retrieval/metrics.py`). Latency chỉ tính retrieval(+rerank), KHÔNG gồm embed query (đã cache) — p95 API thật ở Phase 5 sẽ cao hơn.

| config | mode | rerank | recall@5 | hit rate | MRR | nDCG@5 | p50 ms | p95 ms |
|---|---|---|---:|---:|---:|---:|---:|---:|
| hybrid_rrf_structure_aware **(best)** | hybrid_rrf | none | 0.906 | 0.920 | 0.763 | 0.787 | 5.4 | 18.7 |
| hybrid_rrf_fixed | hybrid_rrf | none | 0.871 | 0.876 | 0.659 | 0.700 | 7.0 | 27.7 |
| hybrid_rrf_parent_child | hybrid_rrf | none | 0.871 | 0.885 | 0.756 | 0.779 | 5.4 | 20.4 |
| hybrid_rrf_recursive | hybrid_rrf | none | 0.857 | 0.861 | 0.642 | 0.686 | 7.0 | 24.9 |

- Best config: **hybrid_rrf_structure_aware** — recall@5=0.906, nDCG@5=0.787 (ĐẠT target recall >= 0.85 của metric_definitions.md).
- Số câu đánh giá: 249 (câu không-refusal có citation khớp được).

## Phân tích lỗi — câu hit@5=0 với best config (20 câu)

| question | hỏi | citation kỳ vọng | top-1 nhận được |
|---|---|---|---|
| q_024 | Sinh viên hệ vừa làm vừa học, đại học liên thông khóa tuyển sinh từ 20 | Điều kiện xét tốt nghiệp, mục 1.e | doc_qd1482_quy_che_tin_chi · Điều 33, Khoản 1 |
| q_111 | Ngoài miễn/giảm học phí, IUH còn có chính sách hỗ trợ chi phí học tập  | Chế độ miễn, giảm học phí, mục C, Sổ tay Sinh viên IUH 2024 | doc_sotay_2024 · None |
| q_116 | Sinh viên IUH đạt 82 điểm rèn luyện trong một học kỳ thì được xếp loại | Trích Điều 5, Phân loại kết quả đánh giá rèn luyện, Sổ tay Sinh viên I | doc_sotay_2024 · None |
| q_118 | Sinh viên IUH được khen thưởng theo Quy chế Công tác sinh viên trong n | Trích Điều 7, Khen thưởng sinh viên, Sổ tay Sinh viên IUH 2024 | doc_sotay_2024 · None |
| q_153 | Điểm của em bị sai, giờ phải làm sao? | Điều 26 | doc_qd610_thi_danh_gia · Điều 14, Khoản 3 |
| q_160 | Học phần điều kiện tại IUH gồm những học phần nào, và điểm của các học | Điều 6, Khoản 3 | doc_sotay_2024 · None |
| q_183 | Sinh viên IUH bị xếp loại rèn luyện Kém trong học kỳ xét học bổng thì  | Chế độ học bổng, Học bổng khuyến khích học tập; Trích Điều 5, Phân loạ | doc_faet_hoc_bong_2024 · None |
| q_199 | Em muốn xin học bổng thì cần làm gì? | Chế độ học bổng, Sổ tay Sinh viên IUH 2024 | doc_qd610_thi_danh_gia · Điều 13, Khoản 3-4 |
| q_200 | Em thi trực tuyến mà bị rớt mạng giữa chừng thì tính sao? | Điều 18, Khoản 3 | doc_qd610_thi_danh_gia · Điều 16 |
| q_201 | Em muốn học vượt thì đăng ký thế nào? | Điều 10, Khoản 2 | doc_sotay_2024 · None |
| q_202 | Em bị đình chỉ rồi, giờ có học lại được không? | Điều 24, Khoản 2 | doc_sotay_2024 · None |
| q_207 | Nội quy học đường của IUH được ban hành theo văn bản nào, ngày nào? | Nội quy học đường, Sổ tay Sinh viên IUH 2024 | doc_sotay_2024 · None |
| q_209 | Sinh viên IUH có nguyện vọng xin chuyển sang học tại một trường đại họ | Điều 20, Khoản 1.a | doc_sotay_2024 · None |
| q_211 | Sinh viên khóa tuyển sinh trước năm 2014 tại IUH cần chứng chỉ tiếng A | Điều kiện xét tốt nghiệp, mục 1.e | doc_sotay_2024 · None |
| q_243 | Em muốn xin miễn học một số học phần, có được không? | Điều 31, Khoản 2 | doc_qd1482_quy_che_tin_chi · Điều 11 |
| q_266 | Em học kém tiếng Anh quá, giờ làm sao để tốt nghiệp? | Điều kiện xét tốt nghiệp, mục 1.e | doc_sotay_2024 · None |
| q_270 | Điểm chữ M tại IUH được dùng để ghi nhận trường hợp nào? | Điều 26, Khoản 2.c | doc_tqa_phuc_khao · None |
| q_286 | Sinh viên IUH khi thi giữa học phần bị điểm 0 hoặc bỏ thi không lý do  | Điều 20, Khoản 1.b | doc_qd1482_quy_che_tin_chi · Điều 24 |
| q_287 | Trong trường hợp thiên tai, dịch bệnh phức tạp, việc tổ chức thi giữa  | Điều 20, Khoản 3 | doc_qd1482_quy_che_tin_chi · Điều 15 |
| q_300 | Sinh viên IUH tốt nghiệp sớm hơn thời gian đào tạo tối thiểu quy định  | Điều 4, Khoản 2.b | doc_sotay_2024 · None |