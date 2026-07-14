"""O1-O8 optimization experiment (Phase 11, Module 8) — real RagService runs,
NOT simulated, per docs/system/experiments/experiment_plan.md's "Thực
nghiệm 6". Every config runs through the same 15-question stratified
subset of the golden set (same seed as scripts/run_evaluation.py's smoke
subset, size=15 to bound Gemini quota across 7 live runs — O8 reuses the
already-completed p8 improvement-cycle run instead of re-running).

Usage: python scripts/run_experiment_optimization.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.evaluation import golden_set  # noqa: E402
from src.evaluation.judge import GeminiJudge, JudgeCache  # noqa: E402
from src.evaluation.runner import aggregate, run_question  # noqa: E402
from src.rag.litellm_gateway import LiteLLMGateway  # noqa: E402
from src.rag.prompt_builder import RegistryPromptProvider  # noqa: E402
from src.rag.service import RagService  # noqa: E402
from src.retrieval.citation_matcher import group_chunks_by_document  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"
OUT_PATH = PROJECT_ROOT / "docs" / "system" / "experiments" / "results_optimization_o1_o8.md"
N = 15


def _load_manifest() -> dict:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def _gateway() -> LiteLLMGateway:
    settings = get_settings()
    return LiteLLMGateway(base_url=settings.litellm_base_url, master_key=settings.litellm_master_key)


def _run_config(name: str, items: list[dict], chunks_by_doc, chunk_text_by_id, judge, service, mode="balanced"):
    print(f"\n=== {name} ({len(items)} câu) ===")
    results = []
    t0 = time.perf_counter()
    for i, item in enumerate(items, start=1):
        print(f"  [{i}/{len(items)}] {item['id']} ...", end=" ", flush=True)
        try:
            r = run_question(service, judge, item, chunks_by_doc, chunk_text_by_id, eval_k=service.context_limit, mode=mode)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")
            continue
        results.append(r)
        print(f"refusal={r.got_refusal} cost={r.cost_usd:.5f}")
    elapsed = time.perf_counter() - t0
    agg = aggregate(results, eval_k=service.context_limit)
    agg["_elapsed_s"] = round(elapsed, 1)
    agg["_fallback_hops"] = [r.fallback_hop for r in results]
    agg["_cache_results"] = [
        (service.get_trace(r.trace_id) or {}).get("cache_result") for r in results
    ]
    return agg


def main() -> None:
    settings = get_settings()
    manifest = _load_manifest()
    chunks_path = CHUNKS_DIR / f"{manifest['chunking_strategy_indexed']}_{manifest['data_version']}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    chunks_by_doc = group_chunks_by_document(chunks)
    chunk_text_by_id = {c["chunk_id"]: c["text"] for c in chunks}

    items = golden_set.smoke_subset(golden_set.load_all(), size=N, seed=8)
    print(f"Selected {len(items)} questions (n={N}, seed=8, dùng chung cho mọi config)")

    judge = GeminiJudge(_gateway(), JudgeCache(EVAL_DIR / f"judge_cache_optimization_{manifest['data_version']}.json"))

    all_agg: dict[str, dict] = {}

    # O1 baseline
    svc = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
    )
    all_agg["O1_baseline"] = _run_config("O1 baseline", items, chunks_by_doc, chunk_text_by_id, judge, svc)

    # O2 semantic cache — 2 pass: pass 1 (cold, populates cache), pass 2 (warm)
    svc_cache = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
        enable_semantic_cache=True,
    )
    all_agg["O2_cache_pass1_cold"] = _run_config(
        "O2 semantic cache — pass 1 (cold)", items, chunks_by_doc, chunk_text_by_id, judge, svc_cache
    )
    all_agg["O2_cache_pass2_warm"] = _run_config(
        "O2 semantic cache — pass 2 (warm, repeat same 15 câu)",
        items, chunks_by_doc, chunk_text_by_id, judge, svc_cache
    )

    # O3 context compression
    svc_compress = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
        enable_context_compression=True,
    )
    all_agg["O3_compression"] = _run_config(
        "O3 context compression", items, chunks_by_doc, chunk_text_by_id, judge, svc_compress
    )

    # O4 dynamic top-k
    svc_topk = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
        enable_dynamic_top_k=True,
    )
    all_agg["O4_dynamic_top_k"] = _run_config(
        "O4 dynamic top-k", items, chunks_by_doc, chunk_text_by_id, judge, svc_topk
    )

    # O5 model routing (mode="auto")
    svc_routing = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
    )
    all_agg["O5_routing"] = _run_config(
        "O5 model routing (auto)", items, chunks_by_doc, chunk_text_by_id, judge, svc_routing, mode="auto"
    )

    # O7 combined (cache + compression + dynamic_top_k + routing)
    svc_combined = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
        enable_semantic_cache=True, enable_context_compression=True, enable_dynamic_top_k=True,
    )
    all_agg["O7_combined"] = _run_config(
        "O7 combined", items, chunks_by_doc, chunk_text_by_id, judge, svc_combined, mode="auto"
    )

    # O6 provider fallback — passive: gộp fallback_hop thật từ MỌI config đã
    # chạy ở trên, không giả lập failure riêng (rủi ro/tốn thêm quota không
    # cần thiết khi hệ thống free-tier vốn đã tự fallback khi cần thật).
    # LOẠI "cache" và "n/a" khỏi cả tử số lẫn mẫu số — cache hit/pre-LLM
    # refusal không hề gọi provider, gộp chung với "cần fallback" sẽ SAI
    # (bug thật phát hiện khi chạy: O2 pass2/O7 toàn cache hit -> fallback_hop
    # luôn "cache" -> lẫn vào "not primary" nếu không loại trừ tường minh).
    real_calls = [
        h for agg in all_agg.values() for h in agg.get("_fallback_hops", [])
        if h not in ("cache", "n/a", None)
    ]
    n_fallback = sum(1 for h in real_calls if h != "primary")
    o6_fallback_rate = round(n_fallback / len(real_calls), 3) if real_calls else None

    # O8 feedback-improved — TÁI DÙNG kết quả p8 đã chạy thật ở Part A của
    # Phase 11 (docs/system/experiments/results_prompt_p8_citation_multipart_v1_vs_p7.md),
    # không chạy lại (đã có số liệu thật, n khác n=15 các config khác — ghi rõ).
    p8_summary_path = EVAL_DIR / "eval_smoke_20260714_1403_summary.json"
    o8_summary = json.loads(p8_summary_path.read_text(encoding="utf-8")) if p8_summary_path.exists() else None

    # --- viết report ---
    lines = [
        "# O1-O8 Optimization Experiment (Phase 11, Module 8)",
        "",
        f"Chạy thật (không giả lập) qua RagService thật, {N} câu golden set "
        "(stratified, seed=8 — cùng subset cho mọi config O1-O5/O7). "
        "O6 đo passive (gộp fallback_hop thật từ mọi run trên). O8 tái dùng "
        "kết quả p8_citation_multipart_v1 đã chạy thật ở improvement cycle "
        "(n=48, KHÁC n với các config khác — ghi rõ trong bảng).",
        "",
        "| Config | n | Citation Acc | Faithfulness | Refusal Acc | p95 latency (ms) | Avg cost/req | Cache hit rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, agg in all_agg.items():
        cache_results = agg.get("_cache_results", [])
        n_lookups = sum(1 for c in cache_results if c is not None)
        n_hits = sum(1 for c in cache_results if c == "hit")
        cache_rate = f"{n_hits}/{n_lookups}" if n_lookups else "n/a"
        lines.append(
            f"| {key} | {agg['n_questions']} | {agg.get('citation_accuracy')} | "
            f"{agg.get('faithfulness')} | {agg.get('refusal_accuracy')} | "
            f"{agg.get('p95_latency_ms')} | {agg.get('avg_cost_usd')} | {cache_rate} |"
        )
    if o8_summary:
        lines.append(
            f"| O8_feedback_improved (p8, n khác) | {o8_summary['n_questions']} | "
            f"{o8_summary.get('citation_accuracy')} | {o8_summary.get('faithfulness')} | "
            f"{o8_summary.get('refusal_accuracy')} | {o8_summary.get('p95_latency_ms')} | "
            f"{o8_summary.get('avg_cost_usd')} | n/a |"
        )
    lines += [
        "",
        f"**O6 provider fallback rate (passive, gộp mọi config trên, loại "
        f"trừ cache hit + pre-LLM refusal — không gọi provider):** "
        f"{n_fallback}/{len(real_calls)} = {o6_fallback_rate}",
        "",
        "## Raw aggregate JSON (mỗi config)",
        "",
        "```json",
        json.dumps(
            {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in all_agg.items()},
            ensure_ascii=False, indent=2,
        ),
        "```",
    ]
    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
