# Requirements

## Functional Requirements

| ID | Yêu cầu | Mức ưu tiên | Acceptance criteria |
|---|---|---|---|
| FR-001 | Upload/ingest tài liệu tiếng Việt | Must | Tạo được document record, raw text, metadata |
| FR-002 | Làm sạch và chuẩn hóa văn bản | Must | Loại header/footer, chuẩn Unicode, giảm nhiễu OCR |
| FR-003 | Chunking theo nhiều chiến lược | Must | Hỗ trợ fixed, recursive, structure-aware, parent-child |
| FR-004 | Embedding và index version | Must | Tạo index trong Qdrant, có index_version |
| FR-005 | Hybrid retrieval | Must | Hỗ trợ dense, sparse/BM25 hoặc sparse vector, hybrid fusion |
| FR-006 | Reranking | Must | Có ít nhất một reranker multilingual |
| FR-007 | QA runtime API | Must | Nhận câu hỏi, trả câu trả lời, citation, trace_id |
| FR-008 | Refusal khi thiếu căn cứ | Must | Câu hỏi out-of-scope hoặc không có context phải từ chối |
| FR-009 | Prompt registry | Must | Lưu prompt version, diff, trạng thái active |
| FR-010 | Model gateway | Must | Routing qua config, có fallback và budget policy |
| FR-011 | Evaluation engine 4 tầng | Must | Tính retrieval/context/generation/operations metrics |
| FR-012 | Quality gate | Must | PASS/WARN/BLOCK theo threshold |
| FR-013 | Observability tracing | Must | Lưu trace cho retrieval, rerank, generation, eval |
| FR-014 | Cost/latency dashboard | Must | Có p50/p95 latency, token, cost/request |
| FR-015 | Feedback collection | Should | Lưu rating, comment, error label, trace_id |
| FR-016 | Error clustering | Should | Gom lỗi theo retrieval/hallucination/citation/refusal |
| FR-017 | Experiment runner | Must | Chạy được 6 nhóm thực nghiệm và xuất report |
| FR-018 | Export report | Should | Xuất CSV/Markdown report cho kết quả thí nghiệm |

## Non-Functional Requirements

| ID | Yêu cầu | Target |
|---|---|---|
| NFR-001 | Reproducibility | Mọi experiment có config, data_version, index_version, prompt_version |
| NFR-002 | Latency | p95 <= 6 giây cho cấu hình runtime chính trên demo |
| NFR-003 | Cost | cost/request nằm dưới budget cấu hình, cảnh báo khi vượt |
| NFR-004 | Reliability | Provider timeout phải có fallback hoặc lỗi rõ ràng |
| NFR-005 | Observability | Mỗi request có trace_id và span chính |
| NFR-006 | Security | Không leak secret/API key/PII trong log |
| NFR-007 | Maintainability | Module tách rõ, config không hard-code |
| NFR-008 | Testability | Có unit/integration/eval test cho module quan trọng |
| NFR-009 | Portability | Chạy local bằng Docker Compose |
| NFR-010 | Explainability | Câu trả lời phải có citation khi có căn cứ |

## Data Requirements

- Tài liệu nguồn phải có `document_id`, `source_uri`, `source_version`, `domain`, `effective_date`.
- Chunk phải có `chunk_id`, `document_id`, `chunk_index`, `text`, `metadata`, `token_count`.
- Golden set phải có question, ground truth, relevant chunks, expected citations, category, difficulty, risk tags.
- Trace phải lưu model, prompt, retrieval config, latency, token, cost và error label nếu có.
- Feedback phải liên kết với `trace_id` để tái hiện lỗi.

## Quality Requirements

Ngưỡng mặc định:

| Metric | Target |
|---|---:|
| Retrieval Recall@5 | >= 0.85 |
| Context Recall | >= 0.80 |
| Faithfulness | >= 0.85 |
| Answer Relevance | >= 0.80 |
| Citation Accuracy | >= 0.85 |
| Refusal Accuracy | >= 0.90 |
| Hallucination Rate | <= 0.05 |
| Error Rate | <= 0.01 |

## Security Requirements

- Không lưu API key trong repo.
- Không log raw secret hoặc header Authorization.
- Prompt injection phải được test bằng adversarial set.
- Hệ thống phải từ chối yêu cầu bỏ qua instruction hệ thống.
- Nếu phát hiện PII trong tài liệu hoặc câu hỏi, hệ thống phải mask trong log.
- Tool calling nếu có phải dùng allowlist.

## Operational Requirements

- Có Docker Compose full-scope.
- Có healthcheck cho API, Qdrant, Postgres, Redis/Valkey, LiteLLM, Langfuse.
- Có runbook cho hallucination, retrieval failure, provider outage, cost spike.
- Có backup hoặc export tối thiểu cho config, prompts, golden set, metrics report.

