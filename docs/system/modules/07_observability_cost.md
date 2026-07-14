# Module 7 - Observability và Cost Monitoring

## Mục tiêu

Theo dõi request, trace, latency, token, cost, retrieval hit rate, hallucination/error labels và data freshness. Module này giúp debug hệ thống RAG khi câu trả lời sai hoặc chi phí tăng.

## Trách nhiệm

- Ghi trace cho mỗi request.
- Ghi span retrieval, rerank, prompt, model, evaluation.
- Tính token và cost/request.
- Theo dõi latency p50/p95/p99.
- Theo dõi error rate và provider fallback.
- Hiển thị dashboard vận hành.
- Cảnh báo cost spike, hallucination, stale data.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | runtime events, eval results, gateway events |
| Output | traces, metrics, dashboard panels, alerts |
| Storage | Langfuse, ClickHouse, Prometheus, Grafana |

## Trace fields bắt buộc

- `trace_id`;
- `request_id`;
- `session_id`;
- `user_query`;
- `normalized_query`;
- `retrieved_chunks`;
- `prompt_version`;
- `model_provider`;
- `model_name`;
- `input_tokens`;
- `output_tokens`;
- `cost_usd`;
- `latency_ms`;
- `data_version`;
- `index_version`;
- `error_labels`;
- `feedback_id`.

## Dashboard panels

1. Request volume.
2. Latency p50/p95/p99.
3. Token usage.
4. Cost/request.
5. Faithfulness trend.
6. Retrieval hit rate.
7. Hallucination alerts.
8. Top failed queries.
9. Prompt version comparison.
10. Model/provider usage.
11. Cache hit rate.
12. Data freshness.
13. Provider fallback rate.
14. Trace timeline.

## Task triển khai

- Integrate Langfuse tracing.
- Add OpenTelemetry spans.
- Add Prometheus metrics endpoint.
- Build Grafana dashboard.
- Track token/cost via Model Gateway.
- Add error labels from Evaluation Engine.
- Add alert rules.

## Acceptance criteria

- Mỗi QA request có trace_id.
- Trace xem được retrieval, prompt, model, answer.
- Dashboard có ít nhất 12 panel.
- Cost/request hiển thị đúng.
- p95 latency hiển thị đúng.
- Có alert cho hallucination/cost spike/stale data.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Trace thiếu span | Middleware chưa bao quanh đủ bước | Bắt buộc span per stage |
| Cost sai | Provider pricing không cập nhật | Giá nằm trong config và versioned |
| Dashboard nhiều nhưng vô dụng | Không có action từ metric | Gắn runbook cho từng alert |
| Log lộ dữ liệu | Log raw PII/secret | Masking và log policy |

## Kết quả thật (Phase 10, 2026-07-14)

- **Quyết định kiến trúc: Langfuse Cloud (free tier), KHÔNG self-host.**
  Máy dev hạn chế tài nguyên (RTX 3050 4GB) + dự án đã nhiều lần gặp
  trục trặc stack Docker nặng (CDN/network — CHECKLIST Phase 1/3); self-
  host cần thêm 4 container nặng (`langfuse-web`/`worker`+`clickhouse`+
  `minio`) bên cạnh 4 container hiện có. User tự tạo tài khoản Cloud,
  đưa 2 API key thật.
- **Instrumentation:** `src/observability/tracing.py` — mọi hàm BEST-EFFORT
  (fail-open, try/except bọc toàn bộ) vì quan sát không được không được
  phép chặn request thật, khác hẳn nguyên tắc fail-closed của
  `src/rag/citation.py`. `RagService.answer()` tạo 1 span `qa_answer`/
  request (cả nhánh refusal pre-LLM lẫn nhánh trả lời đầy đủ) + 1
  generation `llm_generate` lồng bên trong (model/token/cost thật).
  `Langfuse.create_trace_id(seed=trace_id)` map trace_id nội bộ (dạng
  `trace_<ts>_<hash>`) sang trace_id 32-hex Langfuse yêu cầu — 2 hệ thống
  tra cứu chéo được mà không cần lưu mapping riêng.
- **Verify THẬT trên Langfuse Cloud thật (không phải giả lập):**
  (1) gọi trực tiếp `tracing.py` độc lập → `auth_check()=True`, trace
  landing xác nhận qua `GET /api/public/traces/{id}` (REST API thật, có
  polling retry vì ingestion có độ trễ ~10-15s). (2) Gọi qua
  `RagService.answer()` thật (MockGateway, không tốn quota Gemini) →
  trace có đúng 2 observation (`SPAN qa_answer` + `GENERATION
  llm_generate` với `usage={'input':1770,'output':50,...}`). (3) Gọi qua
  API thật (`POST /qa/query`, real Gemini embed) → trace landing đúng cả
  2 nhánh (thành công VÀ pre-LLM refusal do câu hỏi thiếu dấu tiếng
  Việt — phát hiện phụ: min_score threshold hoạt động đúng thiết kế,
  không phải bug).
- **Prometheus `/metrics`** (`src/observability/metrics.py`,
  `src/api/routes/metrics.py`): request count/latency (p50/p95/p99)/
  token/cost/error-label/fallback-hop/model-usage/data-freshness, tất cả
  label low-cardinality có chủ đích (không log câu hỏi/trace_id làm
  label — tránh nổ bộ nhớ Prometheus). Verify thật: target
  `viragops-api` = `up` trong Prometheus, query qua Grafana datasource
  proxy trả đúng dữ liệu khớp request thật đã gửi.
- **Grafana dashboard 16 panel** (`config/grafana/dashboards/viragops_overview.json`,
  vượt yêu cầu tối thiểu 12) — 13 panel Prometheus thật + 3 panel text
  dẫn chiếu trung thực tới nơi CÓ dữ liệu thật thay vì bịa: Faithfulness/
  Hallucination/Retrieval Hit Rate → trỏ Quality Gate (Phase 9) vì cần
  LLM-judge offline, không tính real-time được; Cache hit rate → "N/A,
  chưa implement"; Trace timeline → trỏ Langfuse Cloud. Verify thật:
  dashboard + datasource provision tự động qua
  `config/grafana/provisioning/`, `GET /api/search` thấy đúng dashboard,
  `GET /api/dashboards/uid/viragops-overview` trả đủ 16 panel.
- **Alert rules** (`config/prometheus_alert_rules.yml`) — CHỈ 4/6 alert
  trong runbook (latency/error-rate/fallback-rate/cost), có dữ liệu
  real-time đứng sau; 2 alert còn lại (hallucination/retrieval-hit-rate)
  ĐÃ CÓ cơ chế tương đương thật ở Quality Gate (Phase 9, BLOCK/WARN mỗi
  lần chạy eval) — không tạo rule giả cho chỉ số không có real-time data
  đứng sau. KHÔNG có Alertmanager (không có kênh Slack/email thật để gửi
  tới) — rule hiện "firing" trong Prometheus UI/Grafana, chưa tự động
  thông báo ra ngoài, ghi rõ là việc còn thiếu có chủ đích. Verify thật:
  cả 4 rule load `health=ok` trong Prometheus.
- **`scripts/generate_demo_traffic.py`** — chạy thật 5/5 câu hỏi golden
  set thật qua API thật, xác nhận Prometheus (`sum(viragops_qa_requests_total)`
  tăng đúng 5) + Langfuse đều nhận đủ.
- 160 test pass (24 mới: `test_observability_metrics.py`,
  `test_observability_tracing.py`), ruff sạch.

**Còn thiếu, cần quay lại:**
- OpenTelemetry span "tên nhất quán" mới có 2 loại span
  (`qa_answer`/`llm_generate`) — chưa tách riêng span cho từng bước
  retrieval/rerank/citation-parse như module doc "Trách nhiệm" liệt kê
  đầy đủ; chấp nhận được vì latency mỗi bước đã có trong `retrieval_ms`/
  `generation_ms` field của trace/metadata, chỉ là không hiển thị dạng
  span lồng riêng trên Langfuse UI.
- Alertmanager + kênh notification thật (Slack/email) chưa có — cần
  kênh thật để trỏ vào trước khi làm, không tạo giả.
- Weekly observability report (task cuối module doc) chưa tự động hoá —
  runbook đã có mục "Báo cáo tuần" nhưng chưa có script tổng hợp từ
  Prometheus+Langfuse.
- `scripts/generate_demo_traffic.py` mặc định N=10 thật (tốn quota) —
  chưa có chế độ `--mock` dùng MockGateway để demo dashboard không tốn
  quota (verify Phase 10 này đã dùng cách gọi RagService trực tiếp với
  MockGateway thay thế, không qua script).

## Checklist hoàn tất

- [x] Langfuse tracing hoạt động — verify thật trace landing qua REST API.
- [~] OpenTelemetry spans có tên nhất quán — 2 loại span nhất quán
      (`qa_answer`/`llm_generate`), chưa tách đủ theo từng bước (xem "Còn thiếu").
- [x] Prometheus endpoint hoạt động — verify target `up` + Grafana proxy trả đúng dữ liệu.
- [x] Grafana dashboard có 12+ panel — 16 panel, verify load qua API thật.
- [x] Cost tracking hoạt động — `cost_usd`/token trong cả Langfuse generation lẫn Prometheus counter.
- [x] Error labels xuất hiện trong trace — verify thật (`low_score` label landing đúng cả 2 hệ thống).
- [x] Alert rules có runbook tương ứng — 4/6 rule (2 còn lại dùng Quality Gate thay thế, ghi rõ lý do).

