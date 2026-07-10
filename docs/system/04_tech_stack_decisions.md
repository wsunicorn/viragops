# Tech Stack Decisions

## Nguyên tắc chọn công nghệ

- Ưu tiên công cụ open-source hoặc có free/local mode.
- Provider/model phải thay được bằng config.
- Công cụ phải hỗ trợ tracing/evaluation/versioning.
- Hạn chế stack quá nặng nếu không đóng góp cho LLMOps.
- Mọi thành phần phải chạy được bằng Docker Compose hoặc có phương án SaaS thay thế.

## Stack chính

| Thành phần | Chọn chính | Lý do |
|---|---|---|
| Language | Python 3.11+ | Ecosystem AI/ML tốt, nhiều SDK |
| Backend | FastAPI | Async, OpenAPI tự động, dễ test |
| RAG framework | LlamaIndex + LangChain/LangGraph | LlamaIndex mạnh về data/RAG, LangGraph hỗ trợ workflow |
| Vector DB | Qdrant | Hybrid vector, filtering, production-ready |
| Sparse/BM25 | Qdrant sparse hoặc OpenSearch | So sánh hybrid retrieval và BM25 truyền thống |
| Local ablation | FAISS | Nhẹ, phù hợp thí nghiệm local |
| Embedding | BGE-M3 | Đa ngôn ngữ, dense/sparse/multi-vector signals |
| Reranker | bge-reranker-v2-m3, Jina, ViRanker | Reranking quan trọng với tiếng Việt |
| Runtime LLM | GPT-5 mini/GPT-5.4 mini | Cân bằng chi phí/chất lượng |
| Judge LLM | GPT-5.5 hoặc Claude Sonnet/Opus | Dùng cho eval khó, không dùng mọi request |
| Model gateway | LiteLLM Proxy | Multi-provider routing, fallback, budget |
| Evaluation | RAGAS + DeepEval + custom | Kết hợp metric chuẩn và metric riêng |
| Observability | Langfuse + OpenTelemetry + Prometheus/Grafana | Trace LLM, infra metric, dashboard |
| Experiment tracking | MLflow + DVC | Lưu metric, artifact, data version |
| Cache | Redis/Valkey + redis-vl | Semantic cache, queue nhẹ |
| Object store | MinIO/S3 | Lưu raw/processed docs và artifact |
| Workflow | Prefect hoặc Dagster | Lập lịch ingest/eval/nightly job |
| Frontend | Streamlit hoặc Gradio | Demo nhanh, đủ cho khóa luận |

## Quyết định model/provider

Model không được hard-code trong code. Cấu hình model nằm ở `model_gateway.yaml`.

Nhóm model:

- runtime rẻ/nhanh: GPT-5 mini;
- runtime cân bằng: GPT-5.4 mini;
- judge/eval: GPT-5.5 hoặc Claude Sonnet/Opus;
- provider phụ: Gemini Flash;
- open-weight comparison: Qwen3/Gemma/Llama nếu có tài nguyên.

## Quyết định observability

Langfuse dùng cho:

- LLM trace;
- prompt version;
- evaluation score;
- cost/token tracking;
- request-level debugging.

OpenTelemetry dùng để chuẩn hóa span và tránh khóa chặt vào một vendor.

Prometheus/Grafana dùng cho:

- service health;
- CPU/memory;
- request volume;
- latency;
- error rate;
- dashboard vận hành tổng quan.

## Quyết định deployment

Baseline bắt buộc: Docker Compose.

K3s/Kubernetes chỉ làm sau khi hệ thống Compose ổn định và nếu cần minh họa triển khai nâng cao. Không để Kubernetes trở thành blocker cho khóa luận.

## Phương án thay thế

| Thành phần | Phương án thay thế | Khi dùng |
|---|---|---|
| Qdrant | Weaviate, Milvus | Nếu cần feature đặc thù hoặc benchmark |
| Langfuse self-host | Langfuse Cloud | Nếu local Compose quá nặng |
| LiteLLM | OpenRouter hoặc custom gateway | Nếu cần provider aggregation nhanh |
| RAGAS | DeepEval/custom only | Nếu metric RAGAS không phù hợp tiếng Việt |
| Streamlit | Gradio | Nếu muốn chat UI nhanh hơn |

## Rủi ro stack

| Rủi ro | Giảm thiểu |
|---|---|
| Langfuse v3 self-host nhiều service | Dùng compose chính thức làm base, bật từng service |
| API cost cao | Smoke set, cache, model routing, judge sampling |
| Provider thay đổi model | Pin snapshot/model ID tại thời điểm thí nghiệm |
| Reranker chậm | Chỉ rerank top-20, cache kết quả |
| Hybrid retrieval phức tạp | Bắt đầu dense baseline, sau đó thêm sparse/hybrid |

