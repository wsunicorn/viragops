# Metric Definitions

## Retrieval metrics

| Metric | Ý nghĩa | Target |
|---|---|---:|
| Recall@5 | Tỷ lệ relevant chunks được lấy trong top 5 trên tổng relevant chunks (relevant_retrieved / total_relevant) | >= 0.85 |
| MRR | Mean Reciprocal Rank của relevant chunk đầu tiên | >= 0.70 |
| nDCG@5 | Chất lượng xếp hạng top 5 | >= 0.75 |
| Hit Rate | Có retrieved chunk đúng hay không | >= 0.85 |

## Context metrics

| Metric | Ý nghĩa | Target |
|---|---|---:|
| Context Precision | Tỷ lệ context được lấy là liên quan | >= 0.75 |
| Context Recall | Tỷ lệ thông tin cần thiết được context bao phủ | >= 0.80 |
| Context Relevance | Context có phù hợp câu hỏi không | >= 0.80 |

## Generation metrics

| Metric | Ý nghĩa | Target |
|---|---|---:|
| Faithfulness | Answer có bám context không | >= 0.85 |
| Groundedness | Answer có căn cứ từ tài liệu không | >= 0.85 |
| Answer Relevance | Answer có trả lời đúng câu hỏi không | >= 0.80 |
| Citation Accuracy | Citation đúng document/section/chunk không | >= 0.85 |
| Refusal Accuracy | Từ chối đúng khi thiếu căn cứ | >= 0.90 |
| Hallucination Rate | Tỷ lệ answer chứa thông tin ngoài context | <= 0.05 |

## Operations metrics

| Metric | Ý nghĩa | Target |
|---|---|---:|
| p50 latency | Trung vị thời gian phản hồi | <= 3 giây |
| p95 latency | 95% request dưới ngưỡng này | <= 6 giây |
| cost/request | Chi phí trung bình mỗi request | <= 0.005 USD |
| error rate | Tỷ lệ lỗi runtime | <= 0.01 |
| cache hit rate | Tỷ lệ request dùng semantic cache | theo dõi |
| fallback success rate | Tỷ lệ fallback thành công khi provider lỗi | >= 0.90 |

## Feedback metrics

| Metric | Ý nghĩa | Target |
|---|---|---:|
| Satisfaction rate | Tỷ lệ thumbs up | >= 0.80 |
| Negative feedback rate | Tỷ lệ feedback xấu | <= 0.20 |
| Error cluster count | Số cụm lỗi chính | theo dõi |
| Improvement velocity | Thời gian từ lỗi đến fix | <= 1 tuần |

## Regression rules

- Nếu critical metric giảm hơn 3% so với baseline, gate phải BLOCK.
- Nếu warning metric vi phạm nhưng critical đạt, gate WARN.
- Nếu cost giảm nhưng faithfulness/citation accuracy giảm dưới target, không được xem là tối ưu thành công.
- Nếu latency giảm nhờ cache nhưng cache dùng sai data_version, gate BLOCK.

