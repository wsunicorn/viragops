# Module 6 - CI/CD Quality Gate

## Mục tiêu

Chặn các thay đổi làm giảm chất lượng RAG trước khi deploy. Quality Gate biến evaluation thành quyết định vận hành: PASS, WARN hoặc BLOCK.

## Thay đổi phải qua gate

- Prompt mới.
- Model gateway config mới.
- Retrieval config mới.
- Chunking/data/index mới.
- Code runtime thay đổi.
- Guardrail policy thay đổi.

## Input và output

| Loại | Nội dung |
|---|---|
| Input | eval result, baseline metrics, threshold config |
| Output | gate decision, regression report, deploy/block status |
| Storage | GitHub Actions artifact, PostgreSQL, Markdown report |

## Decision policy

- `PASS`: tất cả critical metric đạt, warning metric không giảm nghiêm trọng.
- `WARN`: critical đạt nhưng warning metric vi phạm.
- `BLOCK`: bất kỳ critical metric vi phạm hoặc regression vượt ngưỡng.

Critical metric mặc định:

- Retrieval Recall@5;
- Faithfulness;
- Answer Relevance;
- Hallucination Rate;
- Refusal Accuracy;
- p95 latency;
- error rate.

## Luồng CI

1. PR hoặc config change được tạo.
2. CI phát hiện loại thay đổi.
3. Chạy smoke eval 50 câu.
4. Tính metric.
5. So sánh baseline.
6. Gate quyết định PASS/WARN/BLOCK.
7. Nếu PASS, cho merge/deploy.
8. Nếu WARN, yêu cầu reviewer xác nhận.
9. Nếu BLOCK, giữ version cũ.
10. Nightly job chạy full eval 300 câu.

## Task triển khai

- Tạo `quality_gate.yaml`.
- Implement gate evaluator.
- Implement baseline comparison.
- Implement GitHub Actions workflow.
- Implement Markdown gate report.
- Implement failure case attachment.
- Implement rollback/version keep policy.

## Acceptance criteria

- Gate chạy được từ command line.
- Gate chạy được trong GitHub Actions.
- Gate tạo report rõ PASS/WARN/BLOCK.
- Gate chặn được ít nhất 8 thay đổi xấu giả lập.
- Gate cho pass các thay đổi tốt/trung tính.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Gate quá chặt | Threshold không có margin | Dùng regression margin 2-3% |
| Gate quá lỏng | Chỉ đo answer relevance | Thêm faithfulness/citation/refusal |
| CI quá chậm | Chạy full eval mọi PR | Smoke set 50 câu trong CI, full eval nightly |
| Report khó đọc | Chỉ log console | Xuất Markdown report |

## Kết quả thật (Phase 9, 2026-07-13)

- **Gate là pure function** (`src/qualitygate/gate.py::evaluate_gate()`)
  nhận aggregate dict từ `src/evaluation/report.py::write_summary_json()`
  — không tự chạy eval, không đụng Qdrant/Postgres/LiteLLM, test được
  100% offline.
- **Verify trên số liệu thật**: transcribe số liệu run smoke thật
  (2026-07-13, đã biết trước là xấu vì 100% fallback) vào summary JSON,
  chạy `scripts/check_gate.py` → gate **BLOCK đúng** với đúng 4 lý do
  (hallucination, refusal, latency, error rate) khớp phân tích tay trước
  đó — `docs/system/experiments/results_quality_gate_20260713_0540.md`.
- **16 thay đổi giả lập** (`tests/unit/test_quality_gate.py`, 9 xấu/4
  warning/3 tốt): 9/9 thay đổi xấu bị BLOCK (module doc chỉ yêu cầu
  >=8), 0 false negative, không thay đổi tốt/warning nào bị BLOCK nhầm.
- **Regression margin verify riêng**: 1 metric giảm 0.05 (vẫn > ngưỡng
  tuyệt đối 0.85) nhưng vượt `max_quality_drop=0.03` so baseline → vẫn
  BLOCK — đúng ý đồ "chặn suy giảm từ từ", không chỉ chặn khi chạm đáy.
- **CHƯA làm**: CI chưa thật sự chạy live smoke eval (cần Qdrant snapshot
  + `GEMINI_API_KEY` secret trong GitHub Actions, ngoài phạm vi lần này —
  xem CHECKLIST_IMPLEMENTATION.md Phase 9 "Chưa tốt"); nightly full-eval
  job; baseline tự động chọn; rollback tự động (hiện chỉ dừng ở quyết
  định + report).

## Checklist hoàn tất

- [x] Có quality gate config — `config/quality_gate.yaml`.
- [x] Gate CLI hoạt động — `scripts/check_gate.py`, verify thật với
      summary JSON transcribe từ report thật.
- [ ] GitHub Actions workflow có smoke eval — job offline (test logic +
      16 thay đổi giả lập) đã chạy trong CI; job live-eval-in-CI vẫn
      comment, thiếu hạ tầng (Qdrant snapshot + secret).
- [x] Gate report có metric và decision — Markdown, bảng critical/warning
      + baseline + chi tiết vi phạm.
- [x] Baseline comparison hoạt động — `test_regression_blocks_even_above_absolute_floor`.
- [x] Có test thay đổi tốt/xấu giả lập — 16 case, 9 xấu đều bị chặn.
- [ ] BLOCK giữ version cũ — gate BLOCK dừng ở quyết định + report, chưa
      có bước tự động rollback prompt/config active trong registry.

