"""Calibrate `thresholds.min_score` (config/retrieval.yaml) from REAL trace
data (Phase 8 remediation, 2026-07-13) — `src/rag/service.py` has left this
threshold unenforced since Phase 5 because DBSF fused scores are on a
different scale than the cosine-like values it was originally written for
(see service.py docstring / CHECKLIST Phase 5 "Chưa tốt"); enforcing a
guessed number "blind" risked over-refusing. This script replaces the
guess with a number read off `data/traces/traces.jsonl` (874 real
litellm/gemini traces, excludes MockGateway integration-test traces).

Method: join each trace's question text against data/test_sets/golden_set.jsonl
(exact string match — traces ARE the golden-set questions run through
scripts/run_evaluation.py) to get requires_refusal + expected citations,
then split top-1 retrieved DBSF score into 2 groups:
  - "should_answer": requires_refusal=False AND retrieval actually hit a
    relevant chunk (hit@k via src/retrieval/citation_matcher, same
    ground-truth logic Phase 4/8 already use) -> min_score must NOT refuse
    these, or we lose real recall.
  - "should_refuse": requires_refusal=True (adversarial/out_of_scope) ->
    a good threshold WOULD refuse these on score grounds too, though
    src/rag/service.py already refuses adversarial/out_of_scope mostly via
    the LLM's own refusal branch, not retrieval score, so this is a
    secondary signal, not the primary refusal mechanism.

Prints percentiles for both groups and a suggested threshold (5th
percentile of should_answer's top-1 score, i.e. a cutoff that would have
wrongly refused at most ~5% of real answerable questions in this sample)
plus how many should_refuse cases that threshold would actually catch.
Does NOT edit config/retrieval.yaml automatically — the number is written
to config only after a human reads the printed distribution (same
"no blind config change" principle the un-enforced threshold started from).

Usage:
    python scripts/calibrate_min_score.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.citation_matcher import group_chunks_by_document, match_question  # noqa: E402

TRACES_PATH = PROJECT_ROOT / "data" / "traces" / "traces.jsonl"
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"


def _percentile(values: list[float], pct: float) -> float:
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(len(s) * pct)))
    return s[idx]


def main() -> int:
    golden = [json.loads(x) for x in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_question = {item["question"]: item for item in golden}

    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
    chunks_path = CHUNKS_DIR / f"{manifest['chunking_strategy_indexed']}_{manifest['data_version']}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    chunks_by_doc = group_chunks_by_document(chunks)

    should_answer_scores: list[float] = []
    should_answer_miss_scores: list[float] = []  # answerable nhưng retrieval miss thật (không dùng để chọn threshold)
    should_refuse_scores: list[float] = []
    n_traces_seen = 0
    n_matched = 0

    with TRACES_PATH.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            trace = json.loads(line)
            if trace.get("model_provider") not in ("litellm", "gemini"):
                continue  # bỏ trace mock (integration test), không phải chạy thật
            n_traces_seen += 1
            item = by_question.get(trace["question"])
            if item is None:
                continue
            retrieved = trace.get("retrieved") or []
            if not retrieved:
                continue
            n_matched += 1
            top1 = max(c["score"] for c in retrieved)

            if item["requires_refusal"]:
                should_refuse_scores.append(top1)
                continue

            retrieved_ids = [c["chunk_id"] for c in retrieved]
            groups = [set(m.chunk_ids) for m in match_question(item, chunks_by_doc)]
            groups = [g for g in groups if g]
            hit = bool(groups) and any(any(cid in g for cid in retrieved_ids) for g in groups)
            if hit or not groups:
                # không có ground-truth citation group (vd multi_hop nhiều nhóm
                # rời) -> không loại, coi là "should_answer" bảo thủ
                should_answer_scores.append(top1)
            else:
                should_answer_miss_scores.append(top1)

    print(f"Traces thật (litellm/gemini): {n_traces_seen}, khớp golden_set theo câu hỏi: {n_matched}")
    print(f"  should_answer (requires_refusal=False, retrieval hit): n={len(should_answer_scores)}")
    print(f"  should_answer nhưng retrieval MISS (không dùng để chọn threshold): n={len(should_answer_miss_scores)}")
    print(f"  should_refuse (requires_refusal=True, adversarial/out_of_scope): n={len(should_refuse_scores)}")

    if not should_answer_scores:
        print("Không đủ dữ liệu should_answer để calibrate.")
        return 1

    for label, values in (
        ("should_answer", should_answer_scores),
        ("should_answer_miss", should_answer_miss_scores),
        ("should_refuse", should_refuse_scores),
    ):
        if not values:
            continue
        pcts = {p: round(_percentile(values, p), 4) for p in (0.01, 0.05, 0.10, 0.25, 0.50)}
        print(f"  {label} top-1 score percentiles: {pcts} (min={min(values):.4f}, max={max(values):.4f})")

    suggested = round(_percentile(should_answer_scores, 0.05), 4)
    caught = sum(1 for s in should_refuse_scores if s < suggested)
    print(
        f"\nGợi ý min_score = {suggested} (p5 của should_answer top-1 score) "
        f"-> sẽ refuse nhầm <=5% câu should_answer thật trong mẫu này, "
        f"bắt được {caught}/{len(should_refuse_scores)} câu should_refuse "
        f"({'nhưng đây KHÔNG phải cơ chế refuse chính cho nhóm này, xem docstring' if should_refuse_scores else 'n/a'})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
