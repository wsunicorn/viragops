# Kết quả experiment: retrieval_reranking

> Sinh bởi `scripts/run_experiment.py` lúc 20260712_0723 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, embedding=`gemini-embedding-001`. Metric tính ở k=5 theo `contracts/metric_definitions.md`; relevance = citation-coverage (xem docstring `src/retrieval/metrics.py`). Latency chỉ tính retrieval(+rerank), KHÔNG gồm embed query (đã cache) — p95 API thật ở Phase 5 sẽ cao hơn.

| config | mode | rerank | recall@5 | hit rate | MRR | nDCG@5 | p50 ms | p95 ms |
|---|---|---|---:|---:|---:|---:|---:|---:|
| hybrid_dbsf_pre40 **(best)** | hybrid_dbsf | none | 0.932 | 0.944 | 0.791 | 0.815 | 6.1 | 18.8 |
| hybrid_rrf_rerank_gemini | hybrid_rrf | gemini_listwise | 0.928 | 0.940 | 0.748 | 0.780 | 998.9 | 61023.1 |
| hybrid_dbsf_pre20 | hybrid_dbsf | none | 0.926 | 0.936 | 0.790 | 0.813 | 5.7 | 17.6 |
| hybrid_rrf_pre20 | hybrid_rrf | none | 0.906 | 0.920 | 0.759 | 0.783 | 5.7 | 19.5 |
| hybrid_rrf_pre40 | hybrid_rrf | none | 0.906 | 0.920 | 0.761 | 0.785 | 6.3 | 19.7 |
| dense_rerank_gemini | dense | gemini_listwise | 0.894 | 0.904 | 0.724 | 0.754 | 961.4 | 1197.9 |
| dense_top5 | dense | none | 0.882 | 0.896 | 0.657 | 0.699 | 4.7 | 21.8 |
| sparse_bm25_top5 | sparse | none | 0.865 | 0.876 | 0.708 | 0.734 | 4.1 | 19.1 |

- Best config: **hybrid_dbsf_pre40** — recall@5=0.932, nDCG@5=0.815 (ĐẠT target recall >= 0.85 của metric_definitions.md).
- Số câu đánh giá: 249 (câu không-refusal có citation khớp được).

## Phân tích lỗi — câu hit@5=0 với best config (14 câu)

| question | hỏi | citation kỳ vọng | top-1 nhận được |
|---|---|---|---|
| q_111 | Ngoài miễn/giảm học phí, IUH còn có chính sách hỗ trợ chi phí học tập  | Chế độ miễn, giảm học phí, mục C, Sổ tay Sinh viên IUH 2024 | doc_sotay_2024 · None |
| q_116 | Sinh viên IUH đạt 82 điểm rèn luyện trong một học kỳ thì được xếp loại | Trích Điều 5, Phân loại kết quả đánh giá rèn luyện, Sổ tay Sinh viên I | doc_sotay_2024 · None |
| q_162 | Sinh viên IUH đã có chứng chỉ tiếng Anh quốc tế đạt trình độ B1 trở lê | Điều 10, Khoản 4 | doc_camnang_chuan_tieng_anh · None |
| q_183 | Sinh viên IUH bị xếp loại rèn luyện Kém trong học kỳ xét học bổng thì  | Chế độ học bổng, Học bổng khuyến khích học tập; Trích Điều 5, Phân loạ | doc_faet_hoc_bong_2024 · None |
| q_199 | Em muốn xin học bổng thì cần làm gì? | Chế độ học bổng, Sổ tay Sinh viên IUH 2024 | doc_faet_hoc_bong_2024 · None |
| q_201 | Em muốn học vượt thì đăng ký thế nào? | Điều 10, Khoản 2 | doc_sotay_2024 · None |
| q_209 | Sinh viên IUH có nguyện vọng xin chuyển sang học tại một trường đại họ | Điều 20, Khoản 1.a | doc_sotay_2024 · None |
| q_211 | Sinh viên khóa tuyển sinh trước năm 2014 tại IUH cần chứng chỉ tiếng A | Điều kiện xét tốt nghiệp, mục 1.e | doc_qd1482_quy_che_tin_chi · Điều 33, Khoản 1 |
| q_243 | Em muốn xin miễn học một số học phần, có được không? | Điều 31, Khoản 2 | doc_sotay_2024 · None |
| q_266 | Em học kém tiếng Anh quá, giờ làm sao để tốt nghiệp? | Điều kiện xét tốt nghiệp, mục 1.e | doc_camnang_dieu_kien_tot_nghiep · None |
| q_270 | Điểm chữ M tại IUH được dùng để ghi nhận trường hợp nào? | Điều 26, Khoản 2.c | doc_sotay_2024 · None |
| q_286 | Sinh viên IUH khi thi giữa học phần bị điểm 0 hoặc bỏ thi không lý do  | Điều 20, Khoản 1.b | doc_qd1482_quy_che_tin_chi · Điều 24 |
| q_287 | Trong trường hợp thiên tai, dịch bệnh phức tạp, việc tổ chức thi giữa  | Điều 20, Khoản 3 | doc_qd1482_quy_che_tin_chi · Điều 15 |
| q_300 | Sinh viên IUH tốt nghiệp sớm hơn thời gian đào tạo tối thiểu quy định  | Điều 4, Khoản 2.b | doc_qd1482_quy_che_tin_chi · Điều 35, Khoản 3-4 |