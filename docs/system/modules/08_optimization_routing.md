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

## Kết quả thật (Phase 11, 2026-07-14)

- **Mọi feature mặc định TẮT** (`RagService.__init__`'s `enable_*` kwargs
  đều `False`, `Settings`'s `*_enabled` fields đều `False`) — đúng nguyên
  tắc "đo trước khi đổi default production" đã dùng cho reranker (Phase 4)
  và `top_k_after` (Phase 8). `config/optimization.yaml` giữ threshold
  (similarity_threshold, max_chars_per_chunk, base_k/max_k) config-driven,
  không hard-code trong code.
- **Semantic cache** (`src/optimization/semantic_cache.py`) — Qdrant
  collection `semantic_cache_{index_version}` (reuse `RagService`'s
  `QdrantClient` VÀ vector embedding đã tính, không gọi Gemini thêm lần
  nào). Verify thật qua server sống: hỏi cùng 1 câu 2 lần → lần 2
  `cache_result=hit`, `cost_usd=0.0`, `routing_policy="cache:balanced"`;
  Prometheus `viragops_semantic_cache_lookups_total{result="miss"}=1`,
  `{result="hit"}=1` khớp đúng. Đổi `prompt_version` → cache miss (filter
  chặt hơn yêu cầu gốc "không dùng sai data_version" — thêm cả
  prompt_version).
- **Context compression** (`src/optimization/compression.py`) — extractive
  thuần (giữ nguyên câu gốc theo lexical overlap với câu hỏi, KHÔNG gọi
  LLM tóm tắt) — tránh cả rủi ro hallucination lẫn tốn quota cho 1 bước
  tối ưu.
- **Dynamic top-k** (`src/optimization/routing.py::dynamic_top_k`) — 1
  lần gọi Qdrant duy nhất (`fetch_limit=max_k`, cắt phía client theo top
  score so `min_score`), không cần round-trip thứ 2.
- **Model routing** (`resolve_tier`, `QARequest.mode="auto"`) — rule-based
  theo độ dài câu + liên từ nối vế (cùng tín hiệu ngôn ngữ đã dùng ở
  multi-hop detection đã revert, nhưng dùng cho mục đích khác/rủi ro thấp
  hơn nhiều: chỉ chọn tier, không đổi retrieval). Verify thật: câu ngắn →
  `cheap`, câu nhiều vế → `strong`.
- **Provider fallback**: đã build+test thật ở Phase 7 — Phase 11 chỉ đo
  passive (O6, gộp `fallback_hop` từ mọi run O1-O7), không giả lập failure
  riêng.
- **Budget hard-block**: verify thật qua script cô lập (`daily_usd` tạm
  $0.0005, KHÔNG sửa `model_gateway.yaml` mặc định `0.0`) — request 1 tốn
  $0.0176 (tier strong), request 2 tự hạ xuống `cheap` +
  `error_labels=["budget_warning","budget_downgrade"]`.
- **O1-O8 report thật**: `scripts/run_experiment_optimization.py`, n=15
  (kiểm soát quota qua 7 lần chạy 1 phiên), xem
  `results_optimization_o1_o8.md` cho số liệu đầy đủ. O8 tái dùng kết quả
  p8 thật (n=48) từ Feedback Loop's improvement cycle thay vì chạy lại.

## Checklist hoàn tất

- [x] Semantic cache hoạt động — verify thật qua server sống + Prometheus.
- [x] Cache key có data_version — VÀ prompt_version (chặt hơn yêu cầu gốc).
- [x] Context compression hoạt động — verify unit+integration test thật.
- [x] Dynamic top-k hoạt động — verify unit+integration test thật.
- [x] Query complexity classifier hoạt động — verify unit test + live `/qa/query mode=auto`.
- [x] Model routing hoạt động — như trên.
- [x] Provider fallback hoạt động — đã verify thật ở Phase 7, đo lại passive ở O6.
- [x] Budget control hoạt động — verify thật qua script cô lập (xem trên).
- [x] Có report trade-off O1-O8 — `results_optimization_o1_o8.md`.

