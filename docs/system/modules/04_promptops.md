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

## Checklist hoàn tất

- [ ] Prompt registry schema có đủ metadata.
- [ ] CRUD prompt hoạt động.
- [ ] Prompt rendering hoạt động.
- [ ] Prompt diff hoạt động.
- [ ] Có 6 prompt variants.
- [ ] Prompt comparison chạy được.
- [ ] Active prompt policy hoạt động.
- [ ] Prompt version xuất hiện trong trace.

