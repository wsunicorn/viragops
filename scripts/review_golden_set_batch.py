"""AI self-review helper for a golden-set batch (Phase 2 methodology, see
docs/system/experiments/golden_set_review.md "Batch 3" audit trail).

Automates the 2 checks that scale (document_id cross-reference, numeric
figure corroboration against real source text) so a human/AI reviewer can
spend their attention on the flagged items instead of re-reading all 224
questions line by line. Does NOT replace judgment — every flag still needs
a human/AI read of the actual source text around the claim; this script
only narrows down where to look.

Usage:
    python scripts/review_golden_set_batch.py                # pending_review only
    python scripts/review_golden_set_batch.py --ids q_077,q_078
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from seed_golden_set_iuh import DOCS  # noqa: E402

GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
SRC_DIR = PROJECT_ROOT / "data" / "processed" / "iuh" / "src_20260710"

_NUMBER_RE = re.compile(r"\d[\d.,]*\d|\d")


def load_source_text(document_id: str) -> str:
    meta = DOCS.get(document_id)
    if not meta:
        return ""
    path = SRC_DIR / meta["source_file"]
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_numbers(text: str) -> list[str]:
    """Pull number-like tokens, normalized (strip trailing separators)."""
    raw = _NUMBER_RE.findall(text)
    cleaned = []
    for tok in raw:
        tok = tok.strip(".,")
        if len(tok) >= 1 and tok not in cleaned:
            cleaned.append(tok)
    return cleaned


def check_doc_ids(item: dict) -> list[str]:
    errors = []
    for doc_id in item.get("relevant_documents", []):
        if doc_id not in DOCS:
            errors.append(f"relevant_documents has unknown document_id '{doc_id}'")
    for cit in item.get("expected_citations", []):
        doc_id = cit.get("document_id")
        if doc_id not in DOCS:
            errors.append(f"expected_citations has unknown document_id '{doc_id}'")
    return errors


_CIT_DIEU_RE = re.compile(r"Điều\s+(\d+)")
_CIT_KHOAN_RE = re.compile(r"Khoản\s+(\d+)")
_SRC_DIEU_RE = re.compile(r"Điều\s+(\d+)[.:]")


def check_citation_sections_exist(item: dict) -> list[str]:
    """Với mỗi expected_citations, xác nhận số Điều (nếu có) THẬT SỰ tồn tại
    trong văn bản nguồn được trích — bắt lỗi gõ nhầm số Điều (loại lỗi đã
    từng phát hiện thủ công ở q_202 trước đây, giờ tự động hoá)."""
    errors = []
    for cit in item.get("expected_citations", []):
        doc_id = cit.get("document_id")
        section = cit.get("section", "")
        if doc_id not in DOCS:
            continue  # đã báo ở check_doc_ids
        m = _CIT_DIEU_RE.search(section)
        if not m:
            continue  # trích theo Mục/tên mục, không phải Điều số -> bỏ qua check này
        dieu_num = m.group(1)
        text = load_source_text(doc_id)
        if f"Điều {dieu_num}." not in text and f"Điều {dieu_num}:" not in text:
            errors.append(f"citation '{section}' -> Điều {dieu_num} không thấy trong nguồn {doc_id}")
    return errors


def check_numbers(item: dict) -> list[str]:
    if item.get("requires_refusal") or not item.get("relevant_documents"):
        return []  # refusal/out-of-scope: không có nguồn để đối chiếu, bỏ qua có chủ đích

    blob = "\n".join(load_source_text(d) for d in item["relevant_documents"])
    if not blob:
        return [f"no source text loaded for {item['relevant_documents']}"]

    numbers = extract_numbers(item["ground_truth"])
    missing = [n for n in numbers if len(n) >= 1 and n not in blob]
    # Số 1 chữ số quá dễ trùng ngẫu nhiên (vd "1" trong "Điều 1") -> chỉ báo
    # số có ý nghĩa hơn (>=2 ký tự, hoặc số có dấu . , /) để giảm false positive.
    missing = [n for n in missing if len(n) >= 2]
    return [f"số '{n}' trong ground_truth không thấy trong nguồn" for n in missing] if missing else []


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ids", default="", help="comma-separated id list; mặc định = mọi pending_review")
    args = parser.parse_args()

    items = [json.loads(x) for x in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    target_ids = {x.strip() for x in args.ids.split(",") if x.strip()}
    scope = [
        it for it in items
        if (it["id"] in target_ids if target_ids else it["review_status"] == "pending_review")
    ]

    print(f"Checking {len(scope)} item(s)")
    n_doc_errors = 0
    n_number_flags = 0
    n_dieu_errors = 0
    for item in scope:
        doc_errors = check_doc_ids(item)
        num_flags = check_numbers(item)
        dieu_errors = check_citation_sections_exist(item)
        if doc_errors or num_flags or dieu_errors:
            print(f"\n[{item['id']}] {item['question'][:80]}")
            for e in doc_errors:
                print(f"  DOC_ID_ERROR: {e}")
                n_doc_errors += 1
            for f in num_flags:
                print(f"  NUMBER_FLAG: {f}")
                n_number_flags += 1
            for d in dieu_errors:
                print(f"  DIEU_ERROR: {d}")
                n_dieu_errors += 1

    print(
        f"\nSummary: {n_doc_errors} doc_id error(s), {n_number_flags} number flag(s), "
        f"{n_dieu_errors} Điều-not-found error(s) across {len(scope)} item(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
