# Module 8 - Optimization và Routing

## Mục tiêu

Giảm chi phí và độ trễ mà vẫn giữ chất lượng bằng semantic cache, context compression, dynamic top-k, model routing và provider fallback.

## Trách nhiệm

- Semantic cache theo query similarity và data_version.
- Context compression để giảm input token.
- Dynamic top-k theo retrieval confidence.
- Model routing theo độ khó câu hỏi.
- Provider fallback khi timeout/rate limit.
- Budget control theo ngày/tháng.
- Đo trade-off cost-latency-quality.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | query, retrieval scores, model policy, budget config |
| Output | optimized route, cache decision, compressed context, cost metrics |
| Storage | Redis/Valkey, PostgreSQL, trace store |

## Optimization strategies

| Strategy | Mục tiêu | Rủi ro |
|---|---|---|
| Semantic Cache | Giảm latency/cost cho câu hỏi tương tự | Cache sai nếu data_version cũ |
| Context Compression | Giảm input tokens | Mất thông tin quan trọng |
| Dynamic Top-k | Giảm context không cần thiết | Recall giảm |
| Model Routing | Dùng model rẻ cho câu dễ | Routing sai làm giảm quality |
| Provider Fallback | Tăng reliability | Provider phụ chất lượng khác |

## Routing policy

Query được phân loại:

- `simple`: câu hỏi factoid, một chunk đủ trả lời;
- `medium`: cần nhiều chunk hoặc citation rõ;
- `hard`: multi-hop, ambiguous, có rủi ro hallucination;
- `eval`: request đánh giá, dùng judge model.

Mapping mặc định:

- simple -> cheap runtime model;
- medium -> balanced runtime model;
- hard -> strong runtime model hoặc tăng retrieval/rerank;
- eval -> judge model.

## Task triển khai

- Implement semantic cache key theo query embedding + data_version.
- Implement cache hit/miss logging.
- Implement context compression.
- Implement query complexity classifier.
- Implement routing policy config.
- Implement provider fallback.
- Implement budget warning/block.
- Implement optimization experiment O1-O8.

## Acceptance criteria

- Cache giảm latency cho câu hỏi lặp lại.
- Cache không dùng khi data_version thay đổi.
- Context compression không làm giảm quality vượt ngưỡng.
- Routing giảm cost trung bình.
- Fallback hoạt động khi provider timeout giả lập.
- Có trade-off report.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Cache trả câu cũ | Không gắn data_version | Cache key bắt buộc có data_version |
| Compression làm mất căn cứ | Tóm tắt quá mạnh | Chỉ compress after retrieval, kiểm citation |
| Routing sai | Classifier đơn giản | Rule + eval feedback, threshold bảo thủ |
| Cost vẫn cao | Judge chạy quá nhiều | Judge sampling và cache eval |

## Checklist hoàn tất

- [ ] Semantic cache hoạt động.
- [ ] Cache key có data_version.
- [ ] Context compression hoạt động.
- [ ] Dynamic top-k hoạt động.
- [ ] Query complexity classifier hoạt động.
- [ ] Model routing hoạt động.
- [ ] Provider fallback hoạt động.
- [ ] Budget control hoạt động.
- [ ] Có report trade-off O1-O8.

