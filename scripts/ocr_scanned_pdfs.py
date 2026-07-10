"""OCR the scanned PDFs flagged by extract_text.py using Gemini multimodal input.

Rationale (see docs/system/modules/01_data_ragops.md): several official IUH
decision documents (e.g. QD 610/QD-DHCN) and the student handbook are
image-only PDFs (verified via pypdf XObject/Font inspection, not an encoding
bug). Proof of concept showed gemini-3.1-flash-lite can read a scanned page
directly and transcribe it with high accuracy (decision number, date,
articles, signatory all correct) - cheaper and simpler than standing up a
Tesseract + Vietnamese-language-pack pipeline.

Long documents (student handbook ~82 pages) are split into page-range
batches so a single call doesn't risk output truncation, using pypdf to cut
sub-PDFs in memory. Rate limiting follows config/model_gateway.yaml.

Usage:
    python scripts/ocr_scanned_pdfs.py --snapshot src_20260710
    python scripts/ocr_scanned_pdfs.py --snapshot src_20260710 --only D3,D8,D10
    python scripts/ocr_scanned_pdfs.py --snapshot src_20260710 --batch-pages 12
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from pypdf import PdfReader, PdfWriter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "iuh"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "iuh"
GATEWAY_CONFIG = PROJECT_ROOT / "config" / "model_gateway.yaml"

OCR_PROMPT = (
    "Day la mot van ban hanh chinh/phap ly tieng Viet dang scan (PDF anh). "
    "Hay trich xuat OCR NGUYEN VAN toan bo noi dung theo dung thu tu trang, "
    "giu nguyen dau tieng Viet, xuong dong, so Dieu/Khoan/Diem. "
    "Voi moi trang, bat dau bang dong '--- Trang {so_trang_trong_file_nay} ---'. "
    "KHONG dien giai, KHONG tom tat, KHONG bo sot noi dung, chi transcribe nguyen van."
)


def load_gateway_route(tier: str = "judge") -> tuple[str, str, int]:
    """Đọc primary/fallback model + rate limit từ config, không hard-code."""
    cfg = yaml.safe_load(GATEWAY_CONFIG.read_text(encoding="utf-8"))
    route = cfg["routes"][tier]
    rpm = cfg["rate_limits"]["requests_per_minute"]
    return route["primary"]["model"], route["fallback"]["model"], rpm


def split_pdf_range(src_path: Path, start: int, end: int) -> bytes:
    """Trả về PDF con (trang [start, end), 0-indexed) dạng bytes."""
    reader = PdfReader(str(src_path))
    writer = PdfWriter()
    for i in range(start, min(end, len(reader.pages))):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


class OcrBlockedError(RuntimeError):
    """Model trả finish_reason bất thường (vd RECITATION) thay vì lỗi HTTP."""


def ocr_call(
    client: genai.Client, models: list[str], pdf_bytes: bytes, max_retries: int = 2
) -> str:
    """Thử lần lượt từng model trong `models` (primary rồi fallback), mỗi model
    retry `max_retries` lần trước khi chuyển sang model kế tiếp.

    Gemini đôi khi chặn output OCR hợp lệ với finish_reason=RECITATION (nghi
    ngờ trùng dữ liệu training) dù không phải lỗi HTTP — coi đây là lỗi cần
    retry/đổi model, không được âm thầm trả về text rỗng.
    """
    last_exc: Exception | None = None
    for model in models:
        for attempt in range(max_retries):
            try:
                resp = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                        OCR_PROMPT,
                    ],
                )
                finish_reason = (
                    resp.candidates[0].finish_reason if resp.candidates else "NO_CANDIDATES"
                )
                if not resp.text or not resp.text.strip():
                    raise OcrBlockedError(f"empty response, finish_reason={finish_reason}")
                return resp.text
            except (ServerError, OcrBlockedError) as exc:
                last_exc = exc
                wait = 5 * (attempt + 1)
                print(f"    [{model} retry {attempt + 1}/{max_retries}] "
                      f"{type(exc).__name__}: {exc}, wait {wait}s")
                time.sleep(wait)
        print(f"    [{model}] exhausted retries, trying next model")
    raise last_exc or RuntimeError("ocr_call failed with no models tried")


def ocr_document(
    client: genai.Client, models: list[str], src_path: Path, batch_pages: int, delay: float
) -> tuple[str, int, list[str]]:
    """OCR toàn bộ PDF, tự động chia batch nếu số trang > batch_pages.

    Mỗi batch độc lập: một batch lỗi (vd recitation-block ở phần mở đầu chung
    chung) không được làm mất các batch khác đã/sẽ OCR thành công. Trả về
    (text_các_batch_ok, api_calls_used, danh_sách_batch_lỗi).
    """
    page_count = len(PdfReader(str(src_path)).pages)
    ranges = (
        [(0, page_count)]
        if page_count <= batch_pages
        else [(s, min(s + batch_pages, page_count)) for s in range(0, page_count, batch_pages)]
    )

    parts = []
    failed_ranges = []
    calls = 0
    for start, end in ranges:
        label = f"trang {start + 1}-{end}/{page_count}"
        print(f"    batch {label}")
        pdf_bytes = (
            src_path.read_bytes() if len(ranges) == 1 else split_pdf_range(src_path, start, end)
        )
        try:
            parts.append(f"--- [batch {label}] ---\n" + ocr_call(client, models, pdf_bytes))
        except Exception as exc:  # noqa: BLE001 - 1 batch lỗi không được chặn batch còn lại
            print(f"    [BATCH FAILED] {label}: {type(exc).__name__}: {exc}")
            failed_ranges.append(label)
        calls += 1
        if (start, end) != ranges[-1]:
            time.sleep(delay)
    return "\n\n".join(parts), calls, failed_ranges


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--only", default="", help="comma-separated doc ids, e.g. D3,D8")
    parser.add_argument("--batch-pages", type=int, default=15)
    parser.add_argument("--tier", default="judge", help="model tier trong model_gateway.yaml")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI_API_KEY not set (check .env is loaded into environment)")
        return 1

    primary, fallback, rpm = load_gateway_route(args.tier)
    models = [primary, fallback]
    delay = max(60.0 / rpm, 3.0)
    print(f"Using models={models} tier={args.tier} (delay={delay:.1f}s between calls)")

    processed_dir = PROCESSED_DIR / args.snapshot
    manifest_path = processed_dir / "processed_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    only_ids = {x.strip() for x in args.only.split(",") if x.strip()}
    snapshot_dir = RAW_DIR / args.snapshot
    client = genai.Client(api_key=api_key)

    prior_ocr_runs = manifest.get("ocr_runs", [])

    def save_manifest() -> None:
        """Ghi manifest ngay sau MỖI document, không chờ hết vòng lặp — nếu
        script crash giữa chừng (rate limit, lỗi mạng), kết quả các document
        đã OCR thành công trước đó không bị mất (đã từng xảy ra với D10)."""
        manifest["ocr_runs"] = prior_ocr_runs + ocr_results
        manifest["ocr_failures"] = ocr_failures
        manifest["summary"]["needs_ocr"] = sum(
            1 for d in manifest["documents"] if d.get("needs_ocr")
        )
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    ocr_results: list[dict] = []
    ocr_failures: list[dict] = []
    for doc in manifest["documents"]:
        if not doc.get("needs_ocr"):
            continue
        if only_ids and doc["doc_id"] not in only_ids:
            continue

        src_path = snapshot_dir / doc["source_file"]
        print(f"\n[OCR] {doc['doc_id']} {doc['source_file']}")
        try:
            text, calls, failed_ranges = ocr_document(
                client, models, src_path, args.batch_pages, delay
            )
        except Exception as exc:  # noqa: BLE001 - lỗi 1 file không được làm hỏng cả batch
            print(f"  [FAILED] {type(exc).__name__}: {exc}")
            ocr_failures.append({"doc_id": doc["doc_id"], "error": str(exc)})
            save_manifest()
            time.sleep(delay)
            continue

        if not text.strip():
            print("  [FAILED] mọi batch đều lỗi, không có text nào để lưu")
            ocr_failures.append(
                {"doc_id": doc["doc_id"], "error": "all batches failed",
                 "failed_ranges": failed_ranges}
            )
            save_manifest()
            time.sleep(delay)
            continue

        txt_filename = doc["txt_file"]  # ghi đè bản .txt gần rỗng bằng bản OCR thật
        (processed_dir / txt_filename).write_text(text, encoding="utf-8")

        result = {
            "doc_id": doc["doc_id"],
            "source_file": doc["source_file"],
            "txt_file": txt_filename,
            "ocr_models_available": models,
            "ocr_api_calls": calls,
            "failed_batches": failed_ranges,   # batch nào bị recitation-block, cần bổ sung thủ công
            "char_count": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "ocr_at": datetime.now(UTC).isoformat(),
        }
        ocr_results.append(result)
        print(f"  -> {len(text):,} chars via {calls} call(s)")

        # cập nhật luôn entry gốc trong danh sách "documents" để processed_manifest nhất quán
        doc["char_count"] = len(text)
        doc["sha256"] = result["sha256"]
        doc["needs_ocr"] = False
        doc["ocr_applied"] = True
        doc["ocr_partial"] = bool(failed_ranges)  # còn batch bị recitation-block, cần chạy lại
        if failed_ranges:
            print(f"  [PARTIAL] {len(failed_ranges)} batch bị block: {failed_ranges}")

        save_manifest()
        time.sleep(delay)

    print(f"\nOCR done: {len(ocr_results)} ok, {len(ocr_failures)} failed -> {manifest_path}")
    return 0 if not ocr_failures else 1


if __name__ == "__main__":
    sys.exit(main())
