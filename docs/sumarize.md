# Tóm tắt toàn diện khóa luận — Nền tảng LLMOps/RAGOps cho hỏi đáp tài liệu tiếng Việt

> File này là **bản đồ tổng thể dễ hình dung** của toàn bộ khóa luận: đọc 1 lần để nắm đề tài, kiến trúc, dữ liệu, thực nghiệm, kế hoạch và cách các tài liệu liên kết với nhau. Chi tiết triển khai nằm ở [llmops_thesis_blueprint.md](llmops_thesis_blueprint.md) và bộ [docs/system/](system/README.md).

---

## 1. Tên đề tài

**VI:** Nghiên cứu, xây dựng và đánh giá nền tảng LLMOps/RAGOps toàn diện cho hệ thống hỏi đáp tài liệu tiếng Việt dựa trên Retrieval-Augmented Generation.

**EN:** Design, Implementation, and Evaluation of a Full-Scope LLMOps/RAGOps Platform for Vietnamese Document Question Answering based on Retrieval-Augmented Generation.

**Tên ngắn:** Nền tảng LLMOps/RAGOps cho hệ thống hỏi đáp tài liệu tiếng Việt.

## 2. Một đoạn tóm tắt

Đề tài xây dựng một hệ thống RAG hỏi đáp tài liệu tiếng Việt **có trích dẫn nguồn**, nhưng điểm cốt lõi **không phải là chatbot demo** mà là **quy trình vận hành LLMOps/RAGOps đầy đủ 9 module** bao quanh nó: quản lý dữ liệu có phiên bản, thực nghiệm retrieval, quản lý prompt, điều phối model, đánh giá tự động, quality gate chặn regression, observability chi phí/độ trễ, tối ưu và vòng lặp phản hồi. Mục tiêu là đưa RAG **từ mức demo sang mức vận hành có kiểm soát**, đo được bằng số liệu định lượng trên domain **quy chế đào tạo + FAQ sinh viên của Trường Đại học Công nghiệp TP.HCM (IUH)**.

## 3. Vấn đề & câu hỏi nghiên cứu

**Vấn đề:** hệ thống RAG demo thường không biết retrieval có đúng không, không đo được hallucination, không version hóa prompt/model/data, không test trước deploy, không theo dõi chi phí/độ trễ, không truy vết được câu trả lời sinh bởi phiên bản nào.

| RQ | Câu hỏi nghiên cứu | Trả lời bởi |
|---|---|---|
| **RQ1** | Cấu hình chunking + retrieval nào tối ưu cho RAG trên văn bản quy chế tiếng Việt có cấu trúc? | Thực nghiệm 1, 2 |
| **RQ2** | Prompt và model/provider nào cân bằng chất lượng – chi phí – độ trễ tốt nhất? | Thực nghiệm 3 |
| **RQ3** | Quality gate có phát hiện & chặn được regression do thay đổi prompt/model/data/retrieval/code không? | Thực nghiệm 4 |
| **RQ4** | Observability/trace có đủ tín hiệu để phân loại nguyên nhân gốc lỗi RAG không? | Thực nghiệm 5 |
| **RQ5** | Có thể giảm chi phí/độ trễ mà vẫn giữ chất lượng bằng cache/compression/routing/feedback không? | Thực nghiệm 6 |

## 4. Domain & dữ liệu (đã chốt: IUH)

Domain chính: **Quy chế đào tạo + Sổ tay/FAQ sinh viên IUH**. Chi tiết nguồn ở [system/experiments/data_sources_iuh.md](system/experiments/data_sources_iuh.md).

| Nguồn | Vai trò | Điểm mạnh |
|---|---|---|
| camnang.iuh.edu.vn | Cẩm nang người học | HTML sạch, có cấu trúc → không cần OCR |
| pdt.iuh.edu.vn | Phòng Đào tạo | Quy chế tín chỉ, học vụ, học bổng, đăng ký học phần |
| ctsv.iuh.edu.vn | Công tác SV | Sổ tay SV, rèn luyện, miễn/giảm học phí |
| tqa.iuh.edu.vn | Khảo thí & ĐBCL | Quy chế thi & đánh giá, phúc khảo |

Nhóm chủ đề: tín chỉ, tốt nghiệp, đăng ký môn, học lại, cảnh báo học vụ, thi/phúc khảo, rèn luyện/kỷ luật, học bổng, học phí/miễn giảm, chuẩn tiếng Anh, bảo lưu/chuyển ngành, và câu hỏi ngoài phạm vi (refusal).

Domain phụ (tùy chọn ~50-100 câu, chứng minh tổng quát hóa): một bộ luật giới hạn (vd Bộ luật Lao động 2019).

## 5. Kiến trúc tổng thể — 9 module

```
                 ┌─────────────────── VÒNG ĐỜI LLMOps/RAGOps ───────────────────┐
                 │                                                              │
  Tài liệu IUH ─▶ [1] DataOps ─▶ [2] Retrieval ─▶ [3] RAG Runtime ─▶ Người dùng │
  (quy chế/FAQ)     ingest         experiment       + [Model Gateway]           │
                    clean/chunk     dense/sparse      citation/refusal          │
                    embed/index     hybrid/rerank         │                     │
                    versioning          │                 ▼                     │
                        │               │           [4] PromptOps               │
                        │               │           (registry/version)          │
                        ▼               ▼                 │                     │
                  [5] Evaluation Engine (4 tầng) ◀────────┘                     │
                   retrieval│context│generation│operations                     │
                        │                                                       │
                        ▼                                                       │
                  [6] CI/CD Quality Gate  ── PASS/WARN/BLOCK ──▶ deploy/rollback │
                        │                                                       │
                        ▼                                                       │
                  [7] Observability/Cost ──▶ trace, dashboard, alert            │
                        │                                                       │
                        ▼                                                       │
                  [8] Optimization/Routing  +  [9] Feedback Loop ───────────────┘
                   cache/compress/route         error cluster → improvement backlog
```

| # | Module | Vai trò | Output chính |
|---|---|---|---|
| 1 | DataOps/RAGOps | Ingest, clean, chunk, embed, index, version | `data_version`, `index_version`, chunks |
| 2 | Retrieval Experiment | So sánh chunking/retrieval/reranking | best retrieval config, metrics |
| 3 | RAG Runtime + Model Gateway | API hỏi đáp, citation, refusal, routing | answer, citations, trace_id |
| 4 | PromptOps | Quản lý prompt lifecycle (P0-P5) | prompt_version, comparison |
| 5 | Evaluation Engine | Đánh giá 4 tầng | eval report, metric scores |
| 6 | CI/CD Quality Gate | Chặn regression trước deploy | PASS/WARN/BLOCK |
| 7 | Observability/Cost | Trace, dashboard 12+ panel, alert | latency, cost, error labels |
| 8 | Optimization/Routing | Cache, compression, routing, fallback | cấu hình tối ưu |
| 9 | Feedback Loop | Thu feedback, phân loại lỗi, cải tiến | improvement backlog |

**Nguyên tắc bất biến:** mọi artifact quan trọng (data, index, prompt, model config, eval, gate) đều có version; mọi thay đổi rủi ro phải qua evaluation + quality gate; không hard-code model (đi qua gateway); không trả lời khi không có căn cứ (refusal).

## 6. Golden set — 300 câu (đóng góp chính)

| Nhóm | Số câu | Mục tiêu |
|---|---:|---|
| Có đáp án | 200 | factoid/procedural/policy QA + citation |
| Không có đáp án | 30 | kiểm tra refusal |
| Adversarial | 20 | prompt injection / ngoài domain |
| Multi-hop | 30 | tổng hợp nhiều chunk |
| Ambiguous | 20 | clarification / nêu giả định |

Split: `smoke` 50 câu (CI nhanh), `full` 300 câu (nightly/milestone), `adversarial` 20, `human_review` 30. Mỗi câu gắn ground truth, relevant chunks, expected citations, category, difficulty, risk tags — trỏ về văn bản IUH.

## 7. Bộ metric & ngưỡng pass/fail (4 tầng)

| Tầng | Metric (ngưỡng) |
|---|---|
| Retrieval | Recall@5 ≥ 0.85 · MRR ≥ 0.70 · nDCG@5 ≥ 0.75 · Hit Rate ≥ 0.85 |
| Context | Context Precision ≥ 0.75 · Context Recall ≥ 0.80 · Context Relevance ≥ 0.80 |
| Generation | Faithfulness ≥ 0.85 · Groundedness ≥ 0.85 · Answer Relevance ≥ 0.80 · Citation Acc ≥ 0.85 · Refusal Acc ≥ 0.90 · Hallucination ≤ 0.05 |
| Operations | p50 ≤ 3s · p95 ≤ 6s · cost/req ≤ $0.005 · error rate ≤ 0.01 |

Quy tắc regression: critical metric giảm > 3% so với baseline → gate **BLOCK**. (Nguồn chuẩn: [contracts/metric_definitions.md](system/contracts/metric_definitions.md).)

## 8. Sáu nhóm thực nghiệm

| # | Thực nghiệm | So sánh | RQ |
|---|---|---|---|
| 1 | Chunking Ablation | 8 cấu hình: fixed 256/512/768, recursive, structure-aware, semantic, parent-child, table-aware | RQ1 |
| 2 | Retrieval + Reranking | dense / BM25 / hybrid RRF/DBSF / + bge/Jina/ViRanker reranker | RQ1-2 |
| 3 | PromptOps + Model/Provider | 6 prompt P0-P5 × nhiều model runtime/judge/provider | RQ2 |
| 4 | Quality Gate Effectiveness | 16 thay đổi giả lập (8 tốt / 8 xấu) → TP/TN/FP/FN | RQ3 |
| 5 | Observability + Error Classification | 300 query + tracing → phân loại nguyên nhân gốc | RQ4 |
| 6 | Cost/Latency/Quality + Feedback | O1-O8: cache, compression, top-k, routing, fallback, feedback | RQ5 |

## 9. Tech stack (rút gọn)

Python 3.11 · FastAPI · LlamaIndex/LangGraph · **Qdrant** (dense/sparse/hybrid) + FAISS · Embedding **BGE-M3** · Reranker bge-reranker-v2-m3/Jina/ViRanker · Model Gateway **LiteLLM** (đa provider, fallback, budget) · Evaluation **RAGAS + DeepEval + custom** + LLM-as-a-Judge · Observability **Langfuse v3 + OpenTelemetry + Prometheus/Grafana** · Experiment tracking **MLflow + DVC** · Cache Redis/Valkey · Object store MinIO · CI **GitHub Actions** · Deploy **Docker Compose** · Frontend Streamlit/Gradio.

> Model runtime/judge (GPT-5.x mini, Claude, Gemini, Qwen3/Gemma/Llama) **không hard-code** — chọn qua `model_gateway.yaml`, pin snapshot tại thời điểm thực nghiệm. Kiểm chứng model ID + URL còn sống trước khi trích dẫn.

## 10. Kế hoạch 24 tuần (12 phase)

| Tuần | Phase | Kết quả |
|---|---|---|
| 1-2 | Khởi tạo project + chuẩn hóa tài liệu | Skeleton, config, healthcheck |
| 3-4 | Dữ liệu IUH + golden set 300 câu | Snapshot nguồn, golden set draft |
| 5-6 | DataOps/RAGOps | Index versioned, data quality report |
| 7-8 | Retrieval Experiment | Best retrieval config |
| 9-10 | RAG Runtime | QA API + citation + refusal + trace |
| 11 | PromptOps | Prompt registry, 6 variants |
| 12 | Model Gateway | Routing, fallback, budget |
| 13-14 | Evaluation Engine | Smoke/full eval, judge |
| 15-16 | CI/CD Quality Gate | Gate + GitHub Actions |
| 17-18 | Observability | Langfuse + Grafana 12+ panel |
| 19-20 | Feedback Loop + Optimization | Error cluster, O1-O8 |
| 21-24 | Chạy 6 thực nghiệm, viết báo cáo, đóng gói demo | Báo cáo + demo full-scope |

Chi tiết từng phase (task, Definition of Done, kiểm tra): [system/CHECKLIST_IMPLEMENTATION.md](system/CHECKLIST_IMPLEMENTATION.md).

## 11. Deliverables

**Kỹ thuật:** Web/API hỏi đáp IUH · DataOps pipeline · Retrieval experiment layer · RAG runtime (citation/refusal/streaming/guardrail) · Prompt registry 6 variants · Model gateway · Evaluation engine 4 tầng · CI/CD quality gate · Observability dashboard 12+ panel · Optimization pipeline · Feedback loop · Docker Compose · **Golden set 300 câu IUH**.

**Báo cáo định lượng:** bảng so sánh 8 chunking, 8 retrieval/reranking, 6 prompt, 6-8 model; quality gate effectiveness; error classification accuracy; cost/latency optimization; feedback improvement; trade-off charts.

**Tài liệu:** báo cáo khóa luận 6 chương (~120-150 trang), README, API docs, ADR.

## 12. Dàn ý báo cáo (6 chương)

1. Giới thiệu (vấn đề, LLMOps, RQ1-5, phạm vi, đóng góp)
2. Cơ sở lý thuyết (LLM, RAG, MLOps→LLMOps→RAGOps, Evaluation, Observability, related work)
3. Phân tích & thiết kế hệ thống (9 module, DB, API, tech stack)
4. Cài đặt hệ thống (từng module + Docker + frontend)
5. Thực nghiệm & đánh giá (6 nhóm + error analysis + trả lời RQ)
6. Kết luận & hướng phát triển

## 13. Bản đồ tài liệu dự án (điều hướng)

```
docs/
├── sumarize.md ............................ (file này) bản đồ tổng thể
├── llmops_thesis_blueprint.md ............. blueprint chi tiết full-scope
├── figures/ ............................... 11 hình (fig_2_1 … fig_4_1)
└── system/
    ├── README.md .......................... hướng dẫn đọc bộ tài liệu
    ├── 00_llmops_fit_assessment.md ........ chấm điểm mức phù hợp LLMOps (8.5/10)
    ├── 01_project_charter.md .............. mục tiêu, phạm vi, domain IUH
    ├── 02_requirements.md ................. FR/NFR, ngưỡng chất lượng
    ├── 03_architecture_overview.md ........ kiến trúc 9 module
    ├── 04_tech_stack_decisions.md ......... lựa chọn công nghệ
    ├── CHECKLIST_IMPLEMENTATION.md ........ 12 phase / 24 tuần
    ├── modules/ (01-09) ................... đặc tả từng module
    ├── contracts/ ........................ api, data, config, metric
    ├── experiments/ ...................... data_sources_iuh, golden_set, plan, report
    └── operations/ ....................... deploy, security, testing, runbooks
```

## 14. Điểm mới & đóng góp

- Không chỉ chatbot RAG mà **quy trình vận hành RAG có kiểm soát** (versioning + eval + quality gate + observability + feedback).
- **Golden set 300 câu tiếng Việt** có kiểm soát cho domain quy chế IUH (ground truth + relevant chunks + expected citations) — lấp khoảng trống "thiếu benchmark RAG tiếng Việt theo domain cụ thể".
- Kết quả thực nghiệm so sánh 15+ cấu hình RAG trên dữ liệu tiếng Việt.
- CI/CD quality gate cho ứng dụng LLM/RAG.
- Hệ thống demo production-like có truy vết, giám sát và cải tiến.

## 15. Tóm tắt một câu

Xây dựng hệ thống RAG hỏi đáp quy chế/FAQ sinh viên IUH tiếng Việt có trích dẫn nguồn, **kèm quy trình LLMOps/RAGOps 9 module** để hệ thống được đánh giá, kiểm thử, giám sát, tối ưu và cải tiến một cách có kiểm soát, đo được bằng số liệu định lượng.
