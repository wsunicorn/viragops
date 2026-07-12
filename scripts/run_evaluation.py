"""Evaluation Engine — Phase 8 (Module 5).

Runs the golden set through the REAL RagService (Phase 5-7 production
code: LiteLLM gateway, Qdrant, prompt registry) and computes all 4 metric
layers per contracts/metric_definitions.md. Every answer costs one real
generation call; faithfulness/relevance additionally cost one real judge
call — this is why `smoke` (stratified 50-question sample) exists for
cheap/CI-speed iteration, with `full` (300) reserved for milestones.

Requires the full stack running (docker compose: qdrant, postgres,
litellm) — same services Phase 5-7 integration tests need.

Usage:
    python scripts/run_evaluation.py --mode smoke
    python scripts/run_evaluation.py --mode full
    python scripts/run_evaluation.py --mode targeted --category adversarial
    python scripts/run_evaluation.py --mode smoke --no-judge   # skip judge calls
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.evaluation import golden_set  # noqa: E402
from src.evaluation import report as report_mod  # noqa: E402
from src.evaluation.judge import GeminiJudge, JudgeCache  # noqa: E402
from src.evaluation.runner import QuestionResult, run_question  # noqa: E402
from src.rag.litellm_gateway import LiteLLMGateway  # noqa: E402
from src.rag.prompt_builder import RegistryPromptProvider  # noqa: E402
from src.rag.service import RagService  # noqa: E402
from src.retrieval.citation_matcher import group_chunks_by_document  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"


def load_manifest() -> dict:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        raise SystemExit("No ingest manifest — run scripts/ingest_data.py first")
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["smoke", "full", "targeted"])
    parser.add_argument("--category", default=None)
    parser.add_argument(
        "--no-judge", action="store_true",
        help="bỏ qua lệnh gọi judge (chỉ tính retrieval/context/refusal, không tốn quota generation cho chất lượng câu trả lời)",
    )
    parser.add_argument(
        "--prompt-version", default=None,
        help="ghim 1 phiên bản prompt cụ thể (kể cả status='testing', chưa activate) thay vì "
        "dùng active version — dùng để so sánh candidate prompt trên eval engine trước khi activate",
    )
    args = parser.parse_args()

    settings = get_settings()
    manifest = load_manifest()

    items = golden_set.select(args.mode, category=args.category)
    print(f"Loaded {len(items)} questions (mode={args.mode})")

    chunks_path = CHUNKS_DIR / f"{manifest['chunking_strategy_indexed']}_{manifest['data_version']}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    chunks_by_doc = group_chunks_by_document(chunks)
    chunk_text_by_id = {c["chunk_id"]: c["text"] for c in chunks}

    service = RagService(
        gateway=LiteLLMGateway(base_url=settings.litellm_base_url, master_key=settings.litellm_master_key),
        qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn, prompt_version=args.prompt_version),
    )

    judge = None
    if not args.no_judge:
        judge_gateway = LiteLLMGateway(base_url=settings.litellm_base_url, master_key=settings.litellm_master_key)
        judge = GeminiJudge(judge_gateway, JudgeCache(EVAL_DIR / f"judge_cache_{manifest['data_version']}.json"))

    meta = {
        "data_version": service.data_version,
        "index_version": service.index_version,
        "retrieval_config_id": service.retrieval_config_id,
        "prompt_version": service._prompt.version,  # noqa: SLF001 - báo cáo cần version thật, không có getter public
    }

    results: list[QuestionResult] = []
    t_start = time.perf_counter()
    for i, item in enumerate(items, start=1):
        print(f"[{i}/{len(items)}] {item['id']} ({item['category']}) ...", end=" ", flush=True)
        try:
            r = run_question(service, judge, item, chunks_by_doc, chunk_text_by_id, eval_k=5)
        except Exception as exc:  # noqa: BLE001 - 1 câu lỗi không được làm sập cả run
            print(f"ERROR: {exc}")
            continue
        results.append(r)
        print(f"refusal={r.got_refusal} refusal_ok={r.refusal_correct}")

    elapsed = time.perf_counter() - t_start
    print(f"\nDone: {len(results)}/{len(items)} scored in {elapsed:.0f}s")

    if not results:
        raise SystemExit("No question scored successfully — check stack (qdrant/postgres/litellm).")

    report_mod.write_outputs(args.mode, results, meta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
