"""Fill golden_set.jsonl's relevant_chunks from real chunk ids (Phase 4).

Closes the P0 gap carried from Phase 3: relevant_chunks stayed empty
because naive exact section matching resolved only 5/71 questions. The
matcher in src/retrieval/citation_matcher.py (structural Điều/Khoản-range
parsing + lexical fallback for section-less documents) resolves 71/71.

relevant_chunks references the DEFAULT indexed strategy's chunk ids
(structure_aware, per config/ingest.yaml) — retrieval experiments on
other strategies recompute their own matches on the fly with the same
matcher (scripts/run_experiment.py), so the JSONL never mixes ids from
different chunk granularities.

Also writes a linking report (data/test_sets/relevant_chunks_report.md)
showing per-citation method (structural vs lexical) so a reviewer can
see exactly how much of the mapping rests on the weaker lexical
heuristic.

Usage:
    python scripts/link_relevant_chunks.py
    python scripts/link_relevant_chunks.py --data-version data_20260711
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.citation_matcher import group_chunks_by_document, match_question  # noqa: E402

GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
REPORT_PATH = PROJECT_ROOT / "data" / "test_sets" / "relevant_chunks_report.md"


def latest_data_version() -> str:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        raise SystemExit("No manifest found — run scripts/ingest_data.py first")
    return manifests[-1].stem.removeprefix("manifest_")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-version", default=None)
    args = parser.parse_args()

    data_version = args.data_version or latest_data_version()
    manifest = json.loads(
        (CHUNKS_DIR / f"manifest_{data_version}.json").read_text(encoding="utf-8")
    )
    strategy = manifest["chunking_strategy_indexed"]
    chunks_path = CHUNKS_DIR / f"{strategy}_{data_version}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_doc = group_chunks_by_document(chunks)

    golden = [
        json.loads(x)
        for x in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]

    method_counts = {"structural": 0, "lexical": 0, "none": 0}
    report_rows: list[str] = []
    linked_questions = 0
    unmatched: list[str] = []

    for item in golden:
        if item.get("requires_refusal"):
            continue
        matches = match_question(item, by_doc)
        all_ids: list[str] = []
        for m in matches:
            method_counts[m.method] += 1
            for cid in m.chunk_ids:
                if cid not in all_ids:
                    all_ids.append(cid)
            report_rows.append(
                f"| {item['id']} | {m.document_id} | {m.section} | {m.method} | {len(m.chunk_ids)} |"
            )
        if all_ids:
            item["relevant_chunks"] = all_ids
            linked_questions += 1
        else:
            unmatched.append(item["id"])

    with GOLDEN_SET_PATH.open("w", encoding="utf-8") as f:
        for item in golden:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    report = [
        "# Relevant chunks linking report",
        "",
        f"> Sinh bởi `scripts/link_relevant_chunks.py` lúc {datetime.now(UTC).isoformat()}.",
        f"> Chunk source: `{chunks_path.name}` (strategy `{strategy}`, {data_version}).",
        "",
        f"- Câu không-refusal đã gán relevant_chunks: **{linked_questions}**",
        f"- Citation khớp structural (parse Điều/Khoản + range): **{method_counts['structural']}**",
        f"- Citation khớp lexical (token-overlap với ground_truth, cho tài liệu "
        f"không có heading Điều): **{method_counts['lexical']}** — mapping yếu hơn, "
        "reviewer nên ưu tiên spot-check nhóm này",
        f"- Citation không khớp được: **{method_counts['none']}**"
        + (f" ({', '.join(unmatched)})" if unmatched else ""),
        "",
        "| question | document | citation section | method | #chunks |",
        "|---|---|---|---|---:|",
        *report_rows,
    ]
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    print(f"Linked {linked_questions} questions -> {GOLDEN_SET_PATH}")
    print(f"methods: {method_counts}")
    print(f"report -> {REPORT_PATH}")
    return 0 if not unmatched else 1


if __name__ == "__main__":
    sys.exit(main())
