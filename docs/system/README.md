# Bộ tài liệu triển khai hệ thống LLMOps/RAGOps

Tài liệu này tách nội dung từ [blueprint gốc](../llmops_thesis_blueprint.md) thành các file triển khai chi tiết. Mục tiêu là dùng bộ tài liệu này như "single source of execution" cho toàn bộ project: đọc để hiểu, làm theo checklist, cài module, chạy thí nghiệm, viết báo cáo và kiểm tra hoàn tất.

## Cách đọc khuyến nghị

1. Đọc `00_llmops_fit_assessment.md` để hiểu đề tài phù hợp với LLMOps ở mức nào và còn thiếu gì.
2. Đọc `01_project_charter.md`, `02_requirements.md`, `03_architecture_overview.md`, `04_tech_stack_decisions.md` để khóa mục tiêu, phạm vi, kiến trúc và stack.
3. Khi bắt đầu code, đọc từng file trong `modules/` theo thứ tự 1 đến 9.
4. Khi cần schema/API/metric, đọc `contracts/`.
5. Khi cần chạy đánh giá và báo cáo số liệu, đọc `experiments/`.
6. Khi triển khai, test, giám sát hoặc xử lý lỗi, đọc `operations/`.
7. Dùng `CHECKLIST_IMPLEMENTATION.md` làm bảng điều khiển chính để thực hiện tuần tự 24 tuần.

## Bản đồ tài liệu

### Tổng quan

| File | Vai trò |
|---|---|
| [00_llmops_fit_assessment.md](00_llmops_fit_assessment.md) | Chấm điểm mức độ phù hợp LLMOps/RAGOps và hành động bổ sung |
| [01_project_charter.md](01_project_charter.md) | Mục tiêu, phạm vi, stakeholder, định nghĩa thành công |
| [02_requirements.md](02_requirements.md) | Yêu cầu chức năng, phi chức năng, dữ liệu, bảo mật, vận hành |
| [03_architecture_overview.md](03_architecture_overview.md) | Kiến trúc 9 module và luồng dữ liệu end-to-end |
| [04_tech_stack_decisions.md](04_tech_stack_decisions.md) | Lựa chọn công nghệ, lý do chọn, phương án thay thế |

### Module triển khai

| Module | File |
|---|---|
| 1. DataOps/RAGOps | [modules/01_data_ragops.md](modules/01_data_ragops.md) |
| 2. Retrieval Experiment | [modules/02_retrieval_experiment.md](modules/02_retrieval_experiment.md) |
| 3. RAG Runtime + Model Gateway integration | [modules/03_rag_runtime_model_gateway.md](modules/03_rag_runtime_model_gateway.md) |
| 4. PromptOps | [modules/04_promptops.md](modules/04_promptops.md) |
| 5. Evaluation Engine | [modules/05_evaluation_engine.md](modules/05_evaluation_engine.md) |
| 6. CI/CD Quality Gate | [modules/06_quality_gate_cicd.md](modules/06_quality_gate_cicd.md) |
| 7. Observability + Cost | [modules/07_observability_cost.md](modules/07_observability_cost.md) |
| 8. Optimization + Routing | [modules/08_optimization_routing.md](modules/08_optimization_routing.md) |
| 9. Feedback Loop | [modules/09_feedback_loop.md](modules/09_feedback_loop.md) |

### Contracts

| File | Nội dung |
|---|---|
| [contracts/api_contracts.md](contracts/api_contracts.md) | API dự kiến cho QA, ingest, eval, prompts, feedback, admin |
| [contracts/data_schemas.md](contracts/data_schemas.md) | Schema tài liệu, chunk, golden set, trace, feedback |
| [contracts/config_schemas.md](contracts/config_schemas.md) | Schema cấu hình retrieval, prompt, model gateway, quality gate |
| [contracts/metric_definitions.md](contracts/metric_definitions.md) | Định nghĩa metric, công thức, ngưỡng pass/fail |

### Thực nghiệm

| File | Nội dung |
|---|---|
| [experiments/data_sources_iuh.md](experiments/data_sources_iuh.md) | Nguồn dữ liệu domain IUH: website, văn bản, ánh xạ category, chiến lược crawl/ingest |
| [experiments/golden_set_design.md](experiments/golden_set_design.md) | Thiết kế golden set 300 câu hỏi |
| [experiments/experiment_plan.md](experiments/experiment_plan.md) | 6 nhóm thực nghiệm full-scope |
| [experiments/result_reporting_template.md](experiments/result_reporting_template.md) | Template báo cáo kết quả và phân tích lỗi |

### Vận hành

| File | Nội dung |
|---|---|
| [operations/deployment_docker_compose.md](operations/deployment_docker_compose.md) | Kế hoạch triển khai Docker Compose full-scope |
| [operations/security_guardrails.md](operations/security_guardrails.md) | Guardrails, prompt injection, PII, OWASP LLM Top 10 |
| [operations/testing_strategy.md](operations/testing_strategy.md) | Unit, integration, e2e, eval tests, CI checks |
| [operations/observability_runbook.md](operations/observability_runbook.md) | Cách đọc trace, metric, dashboard |
| [operations/incident_runbook.md](operations/incident_runbook.md) | Quy trình xử lý hallucination, retrieval failure, cost spike |

## Quy ước triển khai

- Tài liệu này ưu tiên tính triển khai, không phải văn phong báo cáo học thuật.
- Mọi thay đổi lớn trong code sau này phải cập nhật lại tài liệu tương ứng.
- Không hard-code provider/model vào logic nghiệp vụ; mọi model phải đi qua config/model gateway.
- Mọi thay đổi prompt, data, retrieval, model config phải có version và phải chạy quality gate.
- Không deploy nếu critical metric không đạt ngưỡng.

