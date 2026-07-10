# API Contracts

## Quy ước chung

- Base URL local: `http://localhost:8000`.
- Response luôn có `request_id` nếu request hợp lệ.
- QA response luôn có `trace_id`.
- Lỗi trả theo format thống nhất: `error_code`, `message`, `details`.
- Không trả secret, raw API key hoặc prompt nội bộ qua API public.

## Common error response

```json
{
  "request_id": "req_20260602_0001",
  "error_code": "VALIDATION_ERROR",
  "message": "Request không hợp lệ.",
  "details": {
    "field": "question",
    "reason": "question không được rỗng"
  }
}
```

## QA API

### `POST /qa/query`

Mục tiêu: hỏi đáp một câu.

Request:

```json
{
  "question": "Sinh viên cần bao nhiêu tín chỉ để tốt nghiệp?",
  "session_id": "sess_001",
  "user_id": "anonymous",
  "domain": "university_regulation",
  "mode": "balanced",
  "debug": false
}
```

Response:

```json
{
  "request_id": "req_001",
  "trace_id": "trace_001",
  "answer": "Sinh viên cần tích lũy đủ số tín chỉ theo chương trình đào tạo được quy định trong tài liệu.",
  "citations": [
    {
      "document_id": "doc_quy_che_2024",
      "chunk_id": "chunk_042",
      "section": "Điều 12, Khoản 2",
      "page": 8,
      "quote": "..."
    }
  ],
  "confidence": 0.86,
  "refusal": false,
  "model": {
    "provider": "openai",
    "model": "gpt-5.4-mini",
    "routing_policy": "balanced"
  },
  "usage": {
    "input_tokens": 1800,
    "output_tokens": 220,
    "cost_usd": 0.0032,
    "latency_ms": 3120
  }
}
```

### `POST /qa/debug`

Mục tiêu: trả thêm retrieved chunks và prompt metadata để debug.

Chỉ dùng cho admin/dev mode.

Response bổ sung:

```json
{
  "retrieved_chunks": [
    {
      "chunk_id": "chunk_042",
      "score": 0.82,
      "rerank_score": 0.91,
      "text_preview": "..."
    }
  ],
  "prompt_version": "p3_refusal_v2",
  "retrieval_config_id": "hybrid_rrf_rerank_v1",
  "data_version": "data_20260602",
  "index_version": "idx_20260602_bge_m3"
}
```

## Ingest API

### `POST /data/ingest`

Mục tiêu: ingest tài liệu mới hoặc batch tài liệu.

Request:

```json
{
  "domain": "university_regulation",
  "source_uri": "minio://raw/quy_che_2024.pdf",
  "document_type": "pdf",
  "metadata": {
    "title": "Quy chế đào tạo 2024",
    "effective_date": "2024-09-01",
    "owner": "academic_office"
  },
  "chunking_strategy": "structure_aware",
  "run_indexing": true
}
```

Response:

```json
{
  "job_id": "ingest_job_001",
  "document_id": "doc_quy_che_2024",
  "status": "queued"
}
```

### `GET /data/jobs/{job_id}`

Response:

```json
{
  "job_id": "ingest_job_001",
  "status": "completed",
  "data_version": "data_20260602",
  "index_version": "idx_20260602_bge_m3",
  "documents": 1,
  "chunks": 386,
  "quality_errors": []
}
```

## PromptOps API

### `POST /prompts`

Tạo prompt draft.

### `GET /prompts/{prompt_id}/versions`

Liệt kê versions.

### `POST /prompts/{prompt_id}/compare`

Chạy prompt comparison trên smoke/full set.

### `POST /prompts/{prompt_id}/activate`

Chỉ cho phép activate nếu quality gate PASS hoặc có override được ghi log.

## Evaluation API

### `POST /eval/run`

Request:

```json
{
  "eval_mode": "smoke",
  "golden_set_version": "golden_20260602",
  "system_config_id": "sys_cfg_001",
  "run_label": "prompt_p3_candidate"
}
```

Response:

```json
{
  "eval_run_id": "eval_001",
  "status": "queued"
}
```

### `GET /eval/runs/{eval_run_id}`

Response gồm metric tổng hợp và failure cases.

## Quality Gate API

### `POST /quality-gate/check`

Request:

```json
{
  "eval_run_id": "eval_001",
  "baseline_eval_run_id": "eval_base_001",
  "gate_config_id": "gate_default_v1"
}
```

Response:

```json
{
  "gate_run_id": "gate_001",
  "decision": "PASS",
  "critical_failures": [],
  "warnings": ["cost_per_request_usd vượt warning threshold"],
  "report_uri": "minio://reports/gate_001.md"
}
```

## Feedback API

### `POST /feedback`

Request:

```json
{
  "trace_id": "trace_001",
  "rating": "down",
  "category": "citation_error",
  "comment": "Câu trả lời đúng nhưng dẫn nguồn sai điều.",
  "user_id": "anonymous"
}
```

Response:

```json
{
  "feedback_id": "fb_001",
  "status": "accepted",
  "linked_trace_id": "trace_001"
}
```

## Admin/Health API

- `GET /health`: trạng thái API.
- `GET /health/dependencies`: trạng thái Qdrant, Postgres, Redis, LiteLLM, Langfuse.
- `GET /admin/configs`: liệt kê config active.
- `GET /admin/versions`: data/index/prompt/model config active.

