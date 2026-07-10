# Config Schemas

## Retrieval config

```yaml
retrieval_config_id: hybrid_rrf_rerank_v1
data_version: data_20260602
index_version: idx_20260602_bge_m3
query_normalization: true
retrieval:
  type: hybrid
  dense:
    provider: qdrant
    top_k: 20
  sparse:
    provider: qdrant_sparse
    top_k: 20
  fusion:
    method: rrf
    rrf_k: 60
reranker:
  enabled: true
  model: bge-reranker-v2-m3
  top_k_before: 20
  top_k_after: 5
thresholds:
  min_score: 0.15
  min_context_chunks: 2
```

## Prompt config

```yaml
prompt_id: rag_qa_vi
active_version: p3_refusal_v2
domain: university_regulation
task_type: qa
variables:
  - context
  - question
  - citation_format
output_format:
  answer_field: answer
  citations_field: citations
  refusal_field: refusal
policy:
  require_citation: true
  refuse_when_context_insufficient: true
  language: vi
```

## Model gateway config

```yaml
gateway_config_id: gateway_default_v1
default_timeout_seconds: 20
budget:
  daily_usd: 5.0
  monthly_usd: 100.0
routes:
  cheap:
    primary:
      provider: openai
      model: gpt-5-mini
    fallback:
      provider: gemini
      model: gemini-flash
  balanced:
    primary:
      provider: openai
      model: gpt-5.4-mini
    fallback:
      provider: anthropic
      model: claude-sonnet
  strong:
    primary:
      provider: openai
      model: gpt-5.5
    fallback:
      provider: anthropic
      model: claude-opus
  judge:
    primary:
      provider: openai
      model: gpt-5.5
rate_limits:
  requests_per_minute: 60
  tokens_per_minute: 100000
```

## Quality gate config

```yaml
gate_config_id: gate_default_v1
eval_modes:
  ci: smoke
  nightly: full
critical_metrics:
  recall_at_5:
    min: 0.85
  faithfulness:
    min: 0.85
  answer_relevance:
    min: 0.80
  hallucination_rate:
    max: 0.05
  refusal_accuracy:
    min: 0.90
  p95_latency_seconds:
    max: 6.0
  error_rate:
    max: 0.01
warning_metrics:
  citation_accuracy:
    min: 0.85
  cost_per_request_usd:
    max: 0.005
regression:
  max_quality_drop: 0.03
decision:
  deploy_if: all_critical_pass
  warn_if: any_warning_violated
  block_if: any_critical_violated
```

## Experiment config

```yaml
experiment_id: retrieval_ablation_001
golden_set_version: golden_20260602
data_version: data_20260602
configs:
  - retrieval_config_id: dense_baseline_v1
  - retrieval_config_id: hybrid_rrf_v1
  - retrieval_config_id: hybrid_rrf_rerank_v1
metrics:
  - recall_at_5
  - mrr
  - ndcg_at_5
  - context_recall
  - latency_ms
report:
  output_format:
    - csv
    - markdown
```

