"""Mark golden set items as approved, with an explicit audit trail.

review_status transitions are NEVER silent — this script records who/what
approved each item and when, so the provenance stays visible in the data
itself (not just in a commit message). Default reviewer is a human domain
expert per docs/system/experiments/golden_set_design.md; passing
--reviewer ai_self_review is only for the case where the user explicitly
asked an AI assistant to self-review and approve (documented decision,
see golden_set_review.md) instead of doing the manual pass themselves.

Runs validate_golden_set.py's checks first and refuses to approve items
that fail structural/quality validation.

Usage:
    python scripts/approve_golden_set.py --reviewer ai_self_review
    python scripts/approve_golden_set.py --reviewer "Nguyen Van A" --ids q_001,q_002
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_golden_set import DEFAULT_PATH, load_jsonl, validate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--reviewer", required=True, help="tên người/hệ thống review, vd 'ai_self_review'")
    parser.add_argument("--ids", default="", help="comma-separated id list; mặc định approve toàn bộ")
    parser.add_argument("--note", default="", help="ghi chú ngắn gọn về phạm vi/phương pháp review")
    args = parser.parse_args()

    items = load_jsonl(args.path)
    errors = validate(items)
    if errors:
        print(f"REFUSED: {len(errors)} validation error(s) — fix trước khi approve:")
        for e in errors:
            print(f"  - {e}")
        return 1

    target_ids = {x.strip() for x in args.ids.split(",") if x.strip()} or None
    now = datetime.now(UTC).isoformat()
    approved_count = 0

    for item in items:
        if target_ids and item["id"] not in target_ids:
            continue
        item["review_status"] = "approved"
        item["reviewed_by"] = args.reviewer
        item["reviewed_at"] = now
        if args.note:
            item["review_note"] = args.note
        approved_count += 1

    with args.path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"Approved {approved_count}/{len(items)} item(s) by '{args.reviewer}' -> {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
