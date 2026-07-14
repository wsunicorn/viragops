"""Generate demo traffic against the real QA API (Phase 10, Module 7).

Populates Prometheus metrics (GET /metrics) + Langfuse traces (Cloud) with
realistic requests for dashboard demo purposes — samples real golden set
questions across categories (not synthetic filler text) and hits the LIVE
API endpoint (not RagService directly), so metrics/traces reflect exactly
what a real client would produce. Every question costs 1 real generate
call (+ Gemini embedding) — this is not free, keep --n modest.

Usage:
    python scripts/generate_demo_traffic.py --n 10
    python scripts/generate_demo_traffic.py --n 10 --base-url http://localhost:8000
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation import golden_set  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--n", type=int, default=10,
        help="số câu hỏi thật gửi đi (mỗi câu tốn 1 lệnh generate thật, mặc định 10)",
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--delay", type=float, default=1.0, help="giây nghỉ giữa 2 request (tránh rate-limit)")
    parser.add_argument("--seed", type=int, default=None, help="seed random.sample để tái lập mẫu câu hỏi")
    args = parser.parse_args()

    items = golden_set.load_all()
    rng = random.Random(args.seed)
    sample = rng.sample(items, min(args.n, len(items)))

    print(f"Gửi {len(sample)} câu hỏi thật tới {args.base_url}/qa/query ...")
    ok = 0
    with httpx.Client(timeout=30.0) as client:
        for i, item in enumerate(sample, start=1):
            try:
                resp = client.post(f"{args.base_url}/qa/query", json={"question": item["question"]})
                resp.raise_for_status()
                data = resp.json()
                print(
                    f"[{i}/{len(sample)}] {item['id']} ({item['category']}) "
                    f"refusal={data['refusal']} trace_id={data['trace_id']}"
                )
                ok += 1
            except Exception as exc:  # noqa: BLE001 - 1 câu lỗi không được làm sập cả batch
                print(f"[{i}/{len(sample)}] {item['id']} ERROR: {exc}")
            if i < len(sample):
                time.sleep(args.delay)

    print(f"\nDone: {ok}/{len(sample)} request thành công.")
    print(f"Xem metrics thô: {args.base_url}/metrics")
    print("Xem Grafana dashboard: http://localhost:3001/d/viragops-overview")
    print("Xem trace chi tiết: https://cloud.langfuse.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
