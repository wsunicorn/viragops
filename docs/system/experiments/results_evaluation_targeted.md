# Eval report — mode=targeted

> Sinh bởi `scripts/run_evaluation.py` lúc 20260712_1016 UTC. data_version=`data_20260712`, index_version=`idx_20260712_geminiembedding001`, retrieval_config_id=`hybrid_dbsf_v2`, prompt_version=`p6_citation_complete_v1`. Số câu chạy: 20. Chạy qua RagService thật (Phase 5-7) — mỗi câu tốn 1 lệnh generate thật, câu không-refusal tốn thêm 1 lệnh judge thật (0 câu đã chấm, 0 lỗi parse judge).

## Kết quả tổng hợp

| Metric | Giá trị | Target | Verdict |
|---|---:|---:|---|
| Recall@5 | 0.789 | 0.850 | CHƯA ĐẠT |
| Hit rate | 0.789 | | |
| MRR | 0.506 | | |
| Context Precision | 0.168 | 0.750 | CHƯA ĐẠT |
| Context Recall | 0.789 | 0.800 | CHƯA ĐẠT |
| Context Relevance (judge) | n/a | 0.800 |  |
| Faithfulness (judge) | n/a | 0.850 |  |
| Answer Relevance (judge) | n/a | 0.800 |  |
| Citation Accuracy | 0.535 | 0.850 | CHƯA ĐẠT |
| Refusal Accuracy | 1.000 | 0.900 | ĐẠT |
| Hallucination Rate (judge) | n/a | 0.050 |  |
| p50 latency (generation) | 4023 ms | | |
| p95 latency (generation) | 6381 | 6000 | CHƯA ĐẠT |
| Avg cost/req | $0.001027 | <= $0.005 | ĐẠT |
| Error rate | 1.000 | <= 0.01 | CHƯA ĐẠT |
| Fallback rate | 1.000 | (theo dõi) | |
| Cache hit rate | n/a | (theo dõi) | semantic cache chưa implement trong RAG runtime |

> **Lưu ý đọc Context Precision:** mẫu số luôn cố định = số chunk runtime thực trả (`reranker.top_k_after` trong `config/retrieval.yaml`, hiện = 5), trong khi tử số bị chặn trên bởi TỔNG số chunk liên quan thật của câu hỏi (thường 1-3 với câu factoid 1 citation). Ngay cả khi retrieval hoàn hảo (mọi chunk liên quan đều lọt top-5), precision vẫn không thể chạm target 0.75 nếu số chunk liên quan thật < 4 — đây là giới hạn cấu trúc của việc đo precision trên top-k CỐ ĐỊNH với ground truth thưa (citation-based), không phải lỗi retrieval. Context Recall và Hit rate mới là 2 con số phản ánh đúng recall/reachability ở đây.

## Theo category

| Category | n | Recall@k | Refusal Acc | Citation Acc | Faithfulness | Answer Rel. | Hallucination |
|---|---:|---:|---:|---:|---:|---:|---:|
| ambiguous | 20 | 0.789 | 1.000 | 0.535 | n/a | n/a | n/a |

## Failure cases (20 câu, tối đa 30 hiển thị)

| question_id | category | câu hỏi | lý do |
|---|---|---|---|
| q_055 | ambiguous | Em bị rớt môn thì phải làm sao? | trace_error:served_by_fallback:tertiary |
| q_152 | ambiguous | Em muốn bảo lưu kết quả học tập thì cần những điều kiện gì? | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_153 | ambiguous | Điểm của em bị sai, giờ phải làm sao? | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_154 | ambiguous | Em muốn chuyển sang ngành khác thì làm đơn ở đâu? | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_155 | ambiguous | Em bị điểm kém, có bị đuổi học không? | trace_error:served_by_fallback:tertiary |
| q_156 | ambiguous | Học phí kỳ này của em được miễn giảm không? | trace_error:served_by_fallback:tertiary |
| q_157 | ambiguous | Em thi xong thấy đề có vấn đề, giờ tính sao? | trace_error:served_by_fallback:tertiary |
| q_199 | ambiguous | Em muốn xin học bổng thì cần làm gì? | retrieval_miss (hit@k=0); citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_200 | ambiguous | Em thi trực tuyến mà bị rớt mạng giữa chừng thì tính sao? | citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_201 | ambiguous | Em muốn học vượt thì đăng ký thế nào? | retrieval_miss (hit@k=0); citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_202 | ambiguous | Em bị đình chỉ rồi, giờ có học lại được không? | citation_sai (0.33); trace_error:served_by_fallback:tertiary |
| q_203 | ambiguous | Kết quả rèn luyện của em thấp thì có sao không? | trace_error:served_by_fallback:tertiary |
| q_240 | ambiguous | Em muốn chuyển cơ sở học tập thì cần gì? | trace_error:served_by_fallback:tertiary |
| q_241 | ambiguous | Em nộp đơn phúc khảo trễ hạn, giờ có được xét không? | trace_error:served_by_fallback:tertiary |
| q_242 | ambiguous | Học phần của em bị hủy đăng ký, giờ phải làm sao? | citation_sai (0.33); trace_error:served_by_fallback:tertiary |
| q_243 | ambiguous | Em muốn xin miễn học một số học phần, có được không? | retrieval_miss (hit@k=0); citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_266 | ambiguous | Em học kém tiếng Anh quá, giờ làm sao để tốt nghiệp? | retrieval_miss (hit@k=0); citation_sai (0.00); trace_error:served_by_fallback:tertiary |
| q_267 | ambiguous | Em bị lập biên bản trong giờ thi, có ảnh hưởng gì không? | citation_sai (0.50); trace_error:served_by_fallback:tertiary |
| q_296 | ambiguous | Em muốn đăng ký học chương trình thứ hai nhưng chưa biết mình đủ điều kiện chưa, | trace_error:served_by_fallback:tertiary |
| q_297 | ambiguous | Điểm thi của em thấp hơn em nghĩ, em có nên làm đơn không? | trace_error:served_by_fallback:tertiary |