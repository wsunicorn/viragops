"""Prometheus metrics (Phase 10, Module 7) — exposed via GET /metrics
(src/api/routes/metrics.py) using prometheus_client's default registry.

Labels are kept low-cardinality on purpose (prompt_version/refusal/
error-label/fallback-hop — all small closed sets from the registry/gateway
config, never raw question text or trace_id) — an unbounded label value
silently blows up Prometheus memory over time.
"""

from __future__ import annotations

from datetime import datetime

from prometheus_client import Counter, Gauge, Histogram

_LATENCY_BUCKETS = (0.5, 1, 2, 3, 4, 5, 6, 8, 10, 15, 20, 30, 60)

REQUEST_COUNT = Counter(
    "viragops_qa_requests_total", "Tổng số QA request", ["prompt_version", "refusal"]
)
MODEL_USAGE_TOTAL = Counter(
    "viragops_model_usage_total", "Tổng request theo model provider/model đã phục vụ",
    ["provider", "model"],
)
DATA_AGE_DAYS = Gauge(
    "viragops_data_age_days",
    "Số ngày kể từ ingest, parse từ data_version=data_YYYYMMDD — đặt 1 lần lúc RagService khởi động",
)
REQUEST_LATENCY_SECONDS = Histogram(
    "viragops_qa_latency_seconds", "Latency toàn bộ request (giây)", buckets=_LATENCY_BUCKETS
)
RETRIEVAL_LATENCY_SECONDS = Histogram(
    "viragops_retrieval_latency_seconds", "Latency retrieval (giây)"
)
GENERATION_LATENCY_SECONDS = Histogram(
    "viragops_generation_latency_seconds", "Latency generation (giây)", buckets=_LATENCY_BUCKETS
)
TOKENS_TOTAL = Counter("viragops_tokens_total", "Tổng token", ["direction"])  # input|output
COST_USD_TOTAL = Counter(
    "viragops_cost_usd_total", "Tổng cost_usd tích luỹ (giá niêm yết free-tier, xem CHECKLIST Phase 7)"
)
ERROR_TOTAL = Counter("viragops_errors_total", "Tổng lỗi theo error_label", ["label"])
FALLBACK_TOTAL = Counter("viragops_fallback_total", "Tổng request bị phục vụ bởi fallback hop", ["hop"])
RETRIEVED_CHUNKS_COUNT = Histogram(
    "viragops_retrieved_chunks_count", "Số chunk retrieve mỗi request",
    buckets=(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10),
)
CACHE_LOOKUP_TOTAL = Counter(
    "viragops_semantic_cache_lookups_total", "Tổng số lần tra cứu semantic cache (Phase 11)",
    ["result"],  # hit | miss
)


def record_request(trace: dict, total_latency_ms: int) -> None:
    """Gọi 1 lần/request, ngay trước khi RagService.answer() return —
    best-effort giống tracing.py (không raise, không chặn response) vì
    metric thiếu vẫn tốt hơn request lỗi vì lý do quan sát."""
    try:
        prompt_version = trace.get("prompt_version") or "unknown"
        refusal = str(bool(trace.get("refusal")))
        REQUEST_COUNT.labels(prompt_version=prompt_version, refusal=refusal).inc()
        REQUEST_LATENCY_SECONDS.observe(total_latency_ms / 1000)

        retrieval_ms = trace.get("retrieval_ms")
        if retrieval_ms is not None:
            RETRIEVAL_LATENCY_SECONDS.observe(retrieval_ms / 1000)
        generation_ms = trace.get("generation_ms")
        if generation_ms is not None:
            GENERATION_LATENCY_SECONDS.observe(generation_ms / 1000)

        input_tokens = trace.get("input_tokens")
        if input_tokens is not None:
            TOKENS_TOTAL.labels(direction="input").inc(input_tokens)
        output_tokens = trace.get("output_tokens")
        if output_tokens is not None:
            TOKENS_TOTAL.labels(direction="output").inc(output_tokens)

        cost_usd = trace.get("cost_usd")
        if cost_usd is not None:
            COST_USD_TOTAL.inc(cost_usd)

        for label in trace.get("error_labels") or []:
            ERROR_TOTAL.labels(label=label).inc()

        fallback_hop = trace.get("fallback_hop")
        if fallback_hop and fallback_hop not in ("primary", "n/a"):
            FALLBACK_TOTAL.labels(hop=fallback_hop).inc()

        RETRIEVED_CHUNKS_COUNT.observe(len(trace.get("retrieved") or []))

        cache_result = trace.get("cache_result")
        if cache_result:
            CACHE_LOOKUP_TOTAL.labels(result=cache_result).inc()

        provider = trace.get("model_provider")
        model = trace.get("model_name")
        if provider or model:
            MODEL_USAGE_TOTAL.labels(provider=provider or "none", model=model or "none").inc()
    except Exception:  # noqa: BLE001 - quan sát không được không chặn request
        pass


def set_data_version_info(data_version: str | None) -> None:
    """Gọi 1 lần lúc RagService.__init__ (data_version tĩnh suốt vòng đời
    service, không đổi mỗi request) — không đặt trong record_request()."""
    if not data_version:
        return
    try:
        date_str = data_version.removeprefix("data_")
        ingest_date = datetime.strptime(date_str, "%Y%m%d")
        DATA_AGE_DAYS.set((datetime.now() - ingest_date).days)
    except (ValueError, TypeError):
        pass  # data_version không đúng format data_YYYYMMDD -> bỏ qua, không bịa số
