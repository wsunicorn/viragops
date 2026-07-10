# Data Schemas

## Document schema

```json
{
  "document_id": "doc_quy_che_2024",
  "domain": "university_regulation",
  "title": "Quy chế đào tạo 2024",
  "source_uri": "minio://raw/quy_che_2024.pdf",
  "source_type": "pdf",
  "source_version": "src_20260602",
  "effective_date": "2024-09-01",
  "ingested_at": "2026-06-02T10:00:00Z",
  "metadata": {
    "owner": "academic_office",
    "language": "vi",
    "pages": 42
  }
}
```

## Chunk schema

```json
{
  "chunk_id": "chunk_042",
  "document_id": "doc_quy_che_2024",
  "data_version": "data_20260602",
  "chunk_index": 42,
  "text": "Sinh viên cần tích lũy...",
  "normalized_text": "Sinh viên cần tích lũy...",
  "token_count": 286,
  "page_start": 8,
  "page_end": 9,
  "section": "Điều 12, Khoản 2",
  "chunking_strategy": "structure_aware",
  "parent_chunk_id": null,
  "metadata": {
    "heading": "Điều kiện tốt nghiệp",
    "effective_date": "2024-09-01"
  }
}
```

## Golden set item schema

```json
{
  "id": "q_001",
  "question": "Sinh viên cần tích lũy bao nhiêu tín chỉ để tốt nghiệp?",
  "ground_truth": "Sinh viên cần tích lũy đủ số tín chỉ theo chương trình đào tạo.",
  "relevant_chunks": ["chunk_042", "chunk_043"],
  "relevant_documents": ["doc_quy_che_2024"],
  "expected_citations": [
    {
      "document_id": "doc_quy_che_2024",
      "section": "Điều 12, Khoản 2"
    }
  ],
  "category": "factoid",
  "difficulty": "easy",
  "requires_refusal": false,
  "requires_clarification": false,
  "risk_tags": ["graduation", "credits"],
  "review_status": "approved"
}
```

## Trace schema

```json
{
  "trace_id": "trace_001",
  "request_id": "req_001",
  "session_id": "sess_001",
  "question": "Sinh viên cần bao nhiêu tín chỉ để tốt nghiệp?",
  "normalized_query": "sinh viên cần bao nhiêu tín chỉ để tốt nghiệp",
  "data_version": "data_20260602",
  "index_version": "idx_20260602_bge_m3",
  "retrieval_config_id": "hybrid_rrf_rerank_v1",
  "prompt_version": "p3_refusal_v2",
  "model_provider": "openai",
  "model_name": "gpt-5.4-mini",
  "latency_ms": 3120,
  "input_tokens": 1800,
  "output_tokens": 220,
  "cost_usd": 0.0032,
  "answer": "...",
  "citations": ["chunk_042"],
  "error_labels": [],
  "created_at": "2026-06-02T10:00:00Z"
}
```

## Feedback schema

```json
{
  "feedback_id": "fb_001",
  "trace_id": "trace_001",
  "rating": "down",
  "category": "citation_error",
  "comment": "Câu trả lời đúng nhưng dẫn nguồn sai điều.",
  "user_id": "anonymous",
  "review_status": "pending",
  "created_at": "2026-06-02T10:05:00Z"
}
```

## Eval result schema

```json
{
  "eval_run_id": "eval_001",
  "eval_mode": "smoke",
  "golden_set_version": "golden_20260602",
  "system_config_id": "sys_cfg_001",
  "metrics": {
    "recall_at_5": 0.88,
    "mrr": 0.74,
    "context_recall": 0.82,
    "faithfulness": 0.87,
    "answer_relevance": 0.84,
    "citation_accuracy": 0.86,
    "refusal_accuracy": 0.91,
    "hallucination_rate": 0.04,
    "p95_latency_seconds": 5.4,
    "cost_per_request_usd": 0.0038
  },
  "failure_cases_uri": "minio://reports/eval_001_failures.csv"
}
```

