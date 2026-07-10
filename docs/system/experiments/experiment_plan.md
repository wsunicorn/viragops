# Experiment Plan

## Tổng quan

Project chạy 6 nhóm thực nghiệm full-scope để trả lời các câu hỏi nghiên cứu về retrieval, prompt/model, quality gate, observability, cost/latency và feedback loop.

## Thực nghiệm 1 - Chunking Ablation

Mục tiêu: chọn chunking strategy tốt nhất.

Configs:

- fixed 256;
- fixed 512;
- fixed 768;
- recursive;
- structure-aware;
- semantic;
- parent-child;
- table-aware.

Metrics:

- Recall@5;
- MRR;
- nDCG@5;
- Context Recall;
- Citation Accuracy;
- latency retrieval.

## Thực nghiệm 2 - Retrieval Strategy + Reranking

Mục tiêu: so sánh dense, sparse, hybrid và reranking.

Configs:

- dense no rerank;
- BM25/sparse no rerank;
- hybrid RRF no rerank;
- hybrid DBSF no rerank;
- hybrid RRF + bge reranker;
- hybrid RRF + Jina reranker;
- hybrid RRF + ViRanker;
- parent-child + reranker.

## Thực nghiệm 3 - PromptOps + Model/Provider

Mục tiêu: chọn prompt và model/provider theo quality/cost/latency.

Prompt variants:

- P0 naive;
- P1 grounded;
- P2 citation-first;
- P3 refusal-aware;
- P4 self-check;
- P5 concise.

Model/provider:

- GPT-5 mini;
- GPT-5.4 mini;
- GPT-5.5 judge;
- Claude Sonnet/Opus;
- Gemini Flash;
- Qwen3/Gemma/Llama local nếu có.

## Thực nghiệm 4 - Evaluation + Quality Gate

Mục tiêu: kiểm tra gate có chặn regression không.

Thiết kế:

- 16 thay đổi giả lập;
- 8 thay đổi tốt/trung tính;
- 8 thay đổi xấu;
- chạy smoke set trong CI;
- chạy full set cho milestone.

Metrics:

- true positive;
- true negative;
- false positive;
- false negative;
- gate latency;
- regression localization.

## Thực nghiệm 5 - Observability + Error Classification

Mục tiêu: kiểm tra dashboard/trace có đủ debug lỗi không.

Thiết kế:

- chạy 300 queries;
- thu trace đầy đủ;
- gán error labels;
- human review sample;
- đo classification accuracy.

Error labels:

- retrieval_failure;
- context_insufficient;
- hallucination;
- citation_error;
- refusal_error;
- stale_data;
- provider_error;
- cost_latency_issue.

## Thực nghiệm 6 - Cost/Latency/Quality Optimization + Feedback

Mục tiêu: giảm cost/latency mà giữ quality.

Configs:

- O1 baseline;
- O2 semantic cache;
- O3 context compression;
- O4 dynamic top-k;
- O5 model routing;
- O6 provider fallback;
- O7 combined optimized;
- O8 feedback-improved.

Metrics:

- cost/request;
- p95 latency;
- faithfulness;
- citation accuracy;
- cache hit rate;
- fallback success rate;
- quality drop;
- error reduction after feedback.

## Quy tắc báo cáo

- Mỗi experiment phải có config version.
- Mỗi bảng kết quả phải ghi data/index/prompt/model version.
- Mỗi kết luận phải dựa trên metric.
- Nếu kết quả không như kỳ vọng, phải có error analysis.

