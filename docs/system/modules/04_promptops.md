# Module 4 - PromptOps

## Mục tiêu

Quản lý vòng đời prompt như một artifact có version, diff, trạng thái, evaluation và rollback. Prompt không được sửa thủ công trong code mà phải đi qua registry và quality gate.

## Trách nhiệm

- Lưu prompt templates.
- Quản lý prompt versions.
- Gắn prompt với task/domain/model tier.
- So sánh prompt offline.
- Hỗ trợ simulated A/B.
- Chọn prompt active sau quality gate.
- Ghi prompt version trong trace.

## Prompt variants ban đầu

| ID | Tên | Mục tiêu |
|---|---|---|
| P0 | Naive baseline | Đo baseline thấp |
| P1 | Grounded answer | Chỉ trả lời theo context |
| P2 | Citation-first | Ưu tiên trích dẫn nguồn |
| P3 | Refusal-aware | Từ chối khi thiếu căn cứ |
| P4 | Self-check/CoVe-lite | Tự kiểm tra mâu thuẫn |
| P5 | Concise/cost-aware | Giảm token nhưng giữ chất lượng |

## Prompt metadata

Mỗi prompt version cần có:

- `prompt_id`;
- `prompt_version`;
- `task_type`;
- `domain`;
- `language`;
- `model_tier`;
- `template`;
- `variables`;
- `created_by`;
- `created_at`;
- `status`: draft, testing, active, archived;
- `parent_version`;
- `change_summary`;
- `eval_result_id`.

## Luồng thay đổi prompt

1. Tạo prompt draft.
2. Chạy offline comparison trên smoke set.
3. Nếu ổn, chạy full eval 300 câu.
4. Quality gate kiểm tra metric.
5. Nếu PASS, set active.
6. Nếu WARN, reviewer quyết định.
7. Nếu BLOCK, giữ version cũ.
8. Trace runtime ghi prompt active.

## Task triển khai

- Tạo prompt registry schema.
- Implement CRUD prompt.
- Implement prompt rendering với variables.
- Implement prompt diff.
- Implement prompt comparison runner.
- Implement active prompt resolver.
- Integrate với Evaluation Engine.
- Integrate với Quality Gate.

## Acceptance criteria

- Có ít nhất 6 prompt variants.
- Mọi prompt runtime lấy từ registry.
- Prompt version xuất hiện trong trace.
- Có report so sánh prompt.
- Không thể set active prompt nếu chưa có evaluation result hợp lệ.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Prompt sửa trong code | Thiếu registry enforcement | Runtime chỉ nhận prompt từ registry |
| Prompt mới làm giảm quality | Không chạy eval | Bắt buộc quality gate |
| Prompt dài gây cost cao | Template quá nhiều instruction | Có cost-aware prompt và token report |
| LLM không trích dẫn | Output format không rõ | Citation-first prompt |

## Kết quả thật (Phase 6, 2026-07-11)

- **Registry**: bảng `prompts` (PostgreSQL, `sql/migrations/0001_initial_schema.sql`) đủ metadata
  bắt buộc; partial unique index đảm bảo mỗi prompt_id chỉ 1 version
  active kể cả khi ghi đua. Template validate với `variables` khai báo
  ngay lúc ghi (renderer.validate_template) — data hỏng không tới runtime.
- **Activation policy enforce trong code**: không có `eval_result_id` thì
  không activate được, trừ override tường minh có ghi log (actor + lý do
  nối vào change_summary). Bootstrap p1 lúc seed dùng chính cơ chế
  override-logged này, sau đó được THAY bằng activation theo số liệu.
- **Comparison thật (run `promptcmp_20260711_1408`)**: 6 variant × 12 câu
  smoke (8 có đáp án + 2 out-of-scope + 2 adversarial), retrieval dùng
  chung, ~72 lượt gọi flash-lite. Kết quả
  (`experiments/results_prompt_comparison.md`):
  **p1_grounded_v1 thắng** — refusal 1.00, grounded-citation 1.00,
  83.4 token TB (rẻ nhì). Phát hiện đáng chú ý cho báo cáo:
  - `p2_citation_first` refusal **0.00** — quy trình "chọn nguồn trước
    rồi viết" khiến model luôn tìm được *gì đó* để cite và trả lời cả
    câu ngoài phạm vi/adversarial → citation-first tăng grounding cho câu
    trả lời được nhưng PHẢN TÁC DỤNG với refusal.
  - `p3_refusal_aware` chỉ 0.75 refusal — thua p1 dù được thiết kế chuyên
    cho refusal; instruction dài hơn không đồng nghĩa tốt hơn.
  - `p5_concise` refusal 1.00, token rẻ nhất (81.2) nhưng grounded 0.875
    — ứng viên cost-aware nếu Phase 8 xác nhận chất lượng đầy đủ.
  - `p0_naive` đúng vai baseline thấp: refusal 0.50.
- **Runtime không còn prompt hard-code**: `RagService` nhận
  `PromptProvider`; production dùng `RegistryPromptProvider` (resolve
  active từ DB lúc khởi động), test dùng `StaticPromptProvider`. Trace ghi
  `prompt_version` lấy từ registry — verify thật chuỗi registry → runtime
  → trace.
- **API**: POST /prompts, GET /prompts/{id}/versions, GET /prompts/{id}/diff,
  POST /prompts/{id}/activate. `POST /compare` chạy offline qua
  `scripts/run_prompt_comparison.py` (72 lượt LLM không hợp HTTP đồng bộ;
  thành job async khi có eval engine Phase 8).

## Checklist hoàn tất

- [x] Prompt registry schema có đủ metadata — 13 field theo bảng trên + activated_at/by.
- [x] CRUD prompt hoạt động — registry Python + API routes; integration test 5 case trên Postgres thật.
- [x] Prompt rendering hoạt động — `src/promptops/renderer.py`, validate biến lúc ghi, test 6/6 template render sạch.
- [x] Prompt diff hoạt động — unified diff, endpoint GET /prompts/{id}/diff.
- [x] Có 6 prompt variants — P0-P5 seed vào registry, cùng JSON contract để citation parser dùng chung.
- [x] Prompt comparison chạy được — chạy THẬT 6×12, report + CSV, eval_result_id gán ngược vào registry.
- [x] Active prompt policy hoạt động — enforce eval-hoặc-override-logged; p1 active theo số liệu comparison.
- [x] Prompt version xuất hiện trong trace — verify chuỗi registry → runtime → trace.

