-- Phase 11 (Module 9 Feedback Loop) — feedback linked to trace_id, rule-
-- based error taxonomy, human review queue. Feedback KHÔNG sửa production
-- trực tiếp: nó chỉ tạo candidate improvement (xem src/feedback/), mọi
-- thay đổi thật vẫn phải qua PromptOps registry + Evaluation Engine +
-- Quality Gate như các phase trước.

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id     TEXT PRIMARY KEY,
    trace_id        TEXT NOT NULL,
    feedback_type   TEXT NOT NULL
                    CHECK (feedback_type IN (
                        'thumbs_up', 'thumbs_down', 'wrong_answer',
                        'missing_citation', 'outdated_information',
                        'slow_response', 'unsafe_answer'
                    )),
    comment         TEXT,
    rating          INTEGER,
    -- 9 nhãn theo docs/system/modules/09_feedback_loop.md (đối chiếu với
    -- experiment_plan.md's 8-nhãn: thiếu prompt_injection — dùng bản đủ
    -- 9 nhãn ở đây, khớp module doc). NULL cho phép với feedback_type=
    -- 'thumbs_up' (tín hiệu tích cực, không có lỗi để phân loại).
    error_label     TEXT
                    CHECK (error_label IS NULL OR error_label IN (
                        'retrieval_failure', 'context_insufficient', 'hallucination',
                        'citation_error', 'refusal_error', 'stale_data',
                        'prompt_injection', 'provider_error', 'cost_latency_issue'
                    )),
    category        TEXT,
    -- 'user' = feedback thật từ người dùng qua POST /feedback; 'eval_seed'
    -- = suy ra từ eval failure thật (scripts/seed_feedback_from_eval.py) —
    -- ghi rõ nguồn gốc, không trộn lẫn 2 loại khi đọc số liệu.
    source          TEXT NOT NULL DEFAULT 'user' CHECK (source IN ('user', 'eval_seed')),
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'reviewed', 'actioned')),
    reviewed_by     TEXT,
    reviewed_at     TIMESTAMPTZ,
    review_note     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feedback_trace_id ON feedback (trace_id);
CREATE INDEX IF NOT EXISTS idx_feedback_error_label ON feedback (error_label);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback (status);
CREATE INDEX IF NOT EXISTS idx_feedback_category ON feedback (category);
