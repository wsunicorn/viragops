"""Compute distribution stats for the golden set and write golden_set_stats.md.

Usage:
    python scripts/golden_set_stats.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
STATS_OUT_PATH = PROJECT_ROOT / "docs" / "system" / "experiments" / "golden_set_stats.md"

FULL_SET_TARGET = 300
TARGET_GROUPS = {
    "có đáp án (factoid/procedural/multi_hop, không refusal)": 200,
    "không có đáp án (refusal thật sự, không tính data_gap)": 30,
    "adversarial": 20,
    "multi_hop": 30,
    "ambiguous": 20,
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> int:
    if not GOLDEN_SET_PATH.exists():
        print(f"File not found: {GOLDEN_SET_PATH}")
        return 1

    items = load_jsonl(GOLDEN_SET_PATH)
    n = len(items)

    by_category = Counter(i["category"] for i in items)
    by_difficulty = Counter(i["difficulty"] for i in items)
    by_review_status = Counter(i["review_status"] for i in items)
    refusal_count = sum(1 for i in items if i["requires_refusal"])
    clarification_count = sum(1 for i in items if i["requires_clarification"])
    all_tags = Counter(tag for i in items for tag in i["risk_tags"])
    has_answer = sum(1 for i in items if not i["requires_refusal"])
    data_gap = sum(1 for i in items if "data_gap" in i["risk_tags"])
    true_out_of_scope = refusal_count - data_gap

    lines = [
        "# Golden Set — Stats",
        "",
        f"> Tự động sinh bởi `scripts/golden_set_stats.py`. Nguồn: `{GOLDEN_SET_PATH.relative_to(PROJECT_ROOT)}`.",
        "",
        "## Tổng quan",
        "",
        f"- Tổng số câu hiện có: **{n}** / mục tiêu full set **{FULL_SET_TARGET}** "
        f"({n / FULL_SET_TARGET:.0%}).",
        f"- Câu có đáp án (không refusal): {has_answer}.",
        f"- Câu refusal: {refusal_count} (trong đó {data_gap} là *data gap* — domain đúng nhưng "
        f"nguồn chưa ingest đủ; {true_out_of_scope} là *ngoài phạm vi domain thật sự*).",
        f"- Câu cần clarification: {clarification_count}.",
        "",
        "## Phân bố theo category",
        "",
        "| Category | Số câu |",
        "|---|---:|",
    ]
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | {count} |")

    lines += ["", "## Phân bố theo difficulty", "", "| Difficulty | Số câu |", "|---|---:|"]
    for diff, count in sorted(by_difficulty.items(), key=lambda x: -x[1]):
        lines.append(f"| {diff} | {count} |")

    lines += ["", "## Phân bố theo review_status", "", "| Trạng thái | Số câu |", "|---|---:|"]
    for status, count in sorted(by_review_status.items(), key=lambda x: -x[1]):
        lines.append(f"| {status} | {count} |")
    if by_review_status.get("approved", 0) == 0:
        lines.append("")
        lines.append(
            "> ⚠️ **Chưa có câu nào ở trạng thái `approved`.** Theo quy tắc "
            "[golden_set_design.md](golden_set_design.md), chỉ domain expert (người thực hiện "
            "khóa luận) mới được đổi `review_status` sang `approved` sau khi kiểm chứng thủ công "
            "— script này không tự approve."
        )

    lines += ["", "## Phân bố theo risk_tags (chủ đề)", "", "| Tag | Số câu |", "|---|---:|"]
    for tag, count in sorted(all_tags.items(), key=lambda x: -x[1]):
        lines.append(f"| {tag} | {count} |")

    lines += ["", "## So với mục tiêu full set (300 câu, 5 nhóm)", "", "| Nhóm | Hiện có | Mục tiêu |", "|---|---:|---:|"]
    # "Có đáp án" = single-hop factoid/procedural KHÔNG refusal — multi_hop và
    # data_gap (cũng gắn category="factoid") đều là 2 nhóm mục tiêu RIÊNG,
    # không được cộng/gộp vào đây (bug cũ: cộng nhầm cả multi_hop lẫn
    # data_gap-factoid, tổng sai >200 dù đã khớp đúng cơ cấu thiết kế).
    non_refusal_factoid = sum(
        1 for i in items if i["category"] == "factoid" and not i["requires_refusal"]
    )
    counted_answer = non_refusal_factoid + by_category.get("procedural", 0)
    lines.append(
        f"| Có đáp án | {counted_answer} | {TARGET_GROUPS['có đáp án (factoid/procedural/multi_hop, không refusal)']} |"
    )
    lines.append(f"| Không có đáp án (data gap, refusal trong domain) | {data_gap} | {TARGET_GROUPS['không có đáp án (refusal thật sự, không tính data_gap)']} |")
    # golden_set_design.md gộp "ngoài domain" vào chung nhóm adversarial (20
    # câu) — category `out_of_scope` là tập con của bucket này, không phải
    # nhóm mục tiêu thứ 6 riêng.
    adversarial_bucket = by_category.get("adversarial", 0) + by_category.get("out_of_scope", 0)
    lines.append(
        f"| Adversarial (gồm out_of_scope: {by_category.get('out_of_scope', 0)}) | "
        f"{adversarial_bucket} | {TARGET_GROUPS['adversarial']} |"
    )
    lines.append(f"| Multi-hop | {by_category.get('multi_hop', 0)} | {TARGET_GROUPS['multi_hop']} |")
    lines.append(f"| Ambiguous | {by_category.get('ambiguous', 0)} | {TARGET_GROUPS['ambiguous']} |")

    n_linked = sum(1 for i in items if i.get("relevant_chunks"))
    n_citable = sum(1 for i in items if i.get("relevant_documents"))
    lines += [
        "",
        "## Việc còn lại",
        "",
        f"- `relevant_chunks` đã gán cho {n_linked}/{n_citable} câu có căn cứ tài liệu "
        f"({n_linked / n_citable:.1%} nếu > 0) qua `scripts/link_relevant_chunks.py` — phần còn lại "
        "(nếu có) là lexical-miss, xem `data/test_sets/relevant_chunks_report.md`.",
        "- Học phí cụ thể theo ngành/năm và số QĐ học bổng D13 vẫn là data gap thật (chưa có nguồn sạch) "
        "— xem `golden_set_review.md` mục việc còn lại.",
        f"- Theo `review_status`: {by_review_status.get('pending_review', 0)} câu vẫn `pending_review` — "
        "chưa qua domain-expert hay AI self-review có phương pháp. Khuyến nghị domain expert spot-check "
        "trước khi dùng làm baseline chính thức cho báo cáo khóa luận, đặc biệt các con số tín "
        "chỉ/điểm số/phần trăm.",
    ]

    STATS_OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote stats -> {STATS_OUT_PATH}")
    print(f"Total questions: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
