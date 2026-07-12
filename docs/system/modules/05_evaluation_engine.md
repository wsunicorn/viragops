# Module 5 - Evaluation Engine

## Mục tiêu

Xây engine đánh giá RAG 4 tầng: retrieval, context, generation và operations. Evaluation Engine cung cấp số liệu cho experiment, quality gate, dashboard và báo cáo khóa luận.

## 4 tầng đánh giá

| Tầng | Metric |
|---|---|
| Retrieval | Recall@k, MRR, nDCG, Hit Rate |
| Context | Context Precision, Context Recall, Context Relevance |
| Generation | Faithfulness, Answer Relevance, Citation Accuracy, Refusal Accuracy, Hallucination Rate |
| Operations | Latency, cost/request, token usage, error rate, cache hit rate |

## Input và output

| Loại | Nội dung |
|---|---|
| Input | golden set, traces, answers, retrieved chunks, configs |
| Output | eval result, metric scores, failure cases, report |
| Storage | PostgreSQL, MLflow, Langfuse, CSV/Markdown |

## Evaluation modes

- `smoke`: 50 câu, chạy trong CI.
- `full`: 300 câu, chạy nightly hoặc trước milestone.
- `targeted`: subset theo category, dùng debug lỗi.
- `judge_sample`: dùng model judge cho một phần hoặc toàn bộ câu hỏi.
- `human_review`: reviewer kiểm tra mẫu lỗi.

## Luồng xử lý

1. Load eval config.
2. Load golden set subset.
3. Chạy hệ thống hoặc đọc trace có sẵn.
4. Tính retrieval metrics.
5. Tính context metrics.
6. Tính generation metrics bằng RAGAS/DeepEval/custom.
7. Tính operations metrics.
8. Gắn error labels cho case fail.
9. Xuất eval report.
10. Gửi result cho Quality Gate.

## Task triển khai

- Implement golden set loader.
- Implement retrieval metric calculator.
- Implement context metric calculator.
- Integrate RAGAS/DeepEval.
- Implement custom citation/refusal metrics.
- Implement LLM-as-a-Judge wrapper qua Model Gateway.
- Implement eval report writer.
- Implement failure case export.

## Acceptance criteria

- Chạy được smoke eval 50 câu.
- Chạy được full eval 300 câu.
- Có metric theo từng câu và tổng hợp.
- Có failure case list.
- Có eval result ID để quality gate sử dụng.
- Có human review sampling output.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách xử lý |
|---|---|---|
| Judge không nhất quán | LLM-as-a-Judge biến động | Dùng rubric rõ, temperature thấp, human sample |
| Metric không phù hợp tiếng Việt | Tool metric thiên tiếng Anh | Thêm custom metric và manual review |
| Eval quá tốn tiền | Judge mọi câu quá nhiều lần | Smoke set, sampling, cache judge result |
| Result khó phân tích | Chỉ có score tổng | Xuất failure cases và labels |

## Checklist hoàn tất

- [x] Golden set loader hoạt động — `src/evaluation/golden_set.py`.
- [x] Retrieval metrics hoạt động — tái dùng `src/retrieval/metrics.py` (Phase 4).
- [x] Context metrics hoạt động — `src/evaluation/metrics.py` (precision/recall) + judge (relevance).
- [x] Generation metrics hoạt động — judge (faithfulness/answer relevance/hallucination) + deterministic (citation/refusal accuracy).
- [x] Operations metrics hoạt động — latency p50/p95, cost, error rate, fallback rate từ trace thật; `cache_hit_rate` báo `n/a` trung thực (semantic cache chưa implement).
- [x] LLM judge hoạt động — `src/evaluation/judge.py::GeminiJudge`, tier `judge` có sẵn từ Phase 7, cache theo hash.
- [x] Eval report xuất được — `src/evaluation/report.py`, CSV + Markdown.
- [x] Failure cases xuất được — mục "Failure cases" trong report.

## Kết quả thật (smoke, 2026-07-12)

Chạy qua `RagService` thật (không mock, LiteLLM proxy + Qdrant thật), 50
câu stratified theo category thật của golden set 300 câu — số liệu đầy đủ
ở `docs/system/experiments/results_evaluation_smoke.md`.

Tóm tắt (50/50 câu chạy thành công, không sập run nào):

- **Đạt target:** Recall@5=0.905 (>=0.85), Context Recall=0.905 (>=0.80),
  Faithfulness=0.973 (>=0.85), Answer Relevance=0.973 (>=0.80), Context
  Relevance=0.973 (>=0.80), Hallucination Rate=0.027 (<=0.05), p95
  latency generation=1397ms (<=6000ms), cost/req=$0.000746 (<=$0.005).
- **CHƯA đạt target — vấn đề thật, không phải lỗi đo:**
  - **Refusal Accuracy=0.880** (target >=0.90) — 6/50 câu refusal sai,
    cả 2 chiều: q_235/q_236/q_264/q_300 lẽ ra phải refuse (data_gap/thiếu
    căn cứ) nhưng hệ thống vẫn trả lời; q_199 (ambiguous)/q_254
    (multi-hop) lẽ ra phải trả lời nhưng bị refuse. Cần xem lại ngưỡng
    refusal pre-check và/hoặc prompt guardrail — đúng như ghi chú "chưa
    calibrate" trong `src/rag/service.py` Phase 5.
  - **Citation Accuracy=0.838** (target >=0.85) — sát target, đa số lỗi
    rơi vào multi_hop (0.417) — model trích đúng 1 trong 2+ citation kỳ
    vọng nhưng bỏ sót citation còn lại.
  - **Error rate=0.020** (target <=0.01) — 1/50 câu (q_199) model trả
    output không parse được JSON -> hệ thống tự động downgrade thành
    refusal (đúng theo policy `citation.py`), nhưng vẫn tính là lỗi vận
    hành cần giảm.
- **Context Precision=0.189 — KHÔNG so trực tiếp với target 0.75 được:**
  mẫu số cố định = 5 (top_k_after), còn tử số bị chặn trên bởi tổng số
  chunk liên quan thật/câu hỏi (thường 1-3) — xem ghi chú trong report.
  Đây là giới hạn cấu trúc của cách đo, không phải retrieval kém; Context
  Recall/Hit rate mới là số đáng tin ở đây.

## Kết quả thật (full, 298/300 câu, 2026-07-12)

Chạy `--mode full` ngay sau smoke cùng ngày — 3232s (~54 phút), 2 câu lỗi
mạng transient (không phải bug). Số liệu đầy đủ:
`docs/system/experiments/results_evaluation_full.md`.

**Phát hiện quan trọng nhất của lần chạy này KHÔNG phải là một metric số,
mà là một sự cố hạ tầng thật giữa run:** cả 2 Gemini key cạn quota ngày
(dùng chung ngân sách với smoke + Phase 4 chạy trước đó cùng ngày) ở
khoảng câu 272/300 trở đi → LiteLLM tự động fallback: 16 câu qua secondary
key, **19 câu rơi hẳn xuống Ollama local** (đúng thiết kế Phase 7). Số
tổng hợp thô vì vậy bị nhiễu — báo cáo có bảng tách riêng primary (263
câu, sạch) vs fallback (35 câu):

| Nhóm | n | Recall@5 | Citation Acc | Refusal Acc | p95 latency |
|---|---:|---:|---:|---:|---:|
| primary | 263 | 0.940 | 0.781 | **0.962** | 1.49s |
| fallback (secondary+local) | 35 | 0.867 | 0.864* | **0.457** | 23.7s |

*(citation accuracy fallback cao hơn do survivorship bias — câu bị hạ
refusal thì loại khỏi mẫu tính citation accuracy.)*

**Đọc đúng: trên đường primary (88% run, phản ánh đúng chất lượng hệ
thống), Refusal Accuracy=0.962 VƯỢT target 0.90 (còn tốt hơn cả smoke
0.880 — gap ở smoke nhiều khả năng là nhiễu mẫu nhỏ) và p95
latency=1.49s ĐẠT target 6s thoải mái.** Ngược lại, **Citation
Accuracy=0.781 trên đường sạch VẪN dưới target 0.85, nhất quán với smoke
(0.838)** — đây là gap thật cần sửa prompt/service, không phải nhiễu.

**Phát hiện phụ có giá trị cho câu hỏi treo từ Phase 7** ("Ollama fallback
chưa test trên câu phức tạp, chưa biết chất lượng"): giờ có câu trả lời
thật — Ollama (qwen2.5:7b) hay trả JSON có citation không hợp lệ, bị
`citation.py` tự hạ thành refusal (đúng chính sách fail-closed) → nhóm
fallback có refusal_accuracy chỉ 0.457 và latency 23.7s. Fallback "không
crash" (đúng mục tiêu Phase 7) nhưng chất lượng câu trả lời khi thật sự
phải dùng tới nó thì kém hơn đáng kể — cần cân nhắc riêng nếu muốn SLA
chất lượng đồng đều bất kể hop nào phục vụ.

`src/evaluation/report.py::_fallback_note()` đã được thêm để tự động sinh
bảng tách primary/fallback này cho mọi lần chạy sau, không cần vá tay.

