"""Experiment 3 part 2 — Model/Provider Comparison (Phase 12, Module 3).

The prompt-variant half of Experiment 3 is already done (Phases 6/8/11:
p0-p8, comparison reports in docs/system/experiments/). This script does
the other half the blueprint originally planned: comparing models/
providers. This project has NEVER had an OpenAI or Anthropic API key
(config/model_gateway.yaml's own header comment says so), so the
blueprint's GPT-5/Claude/Gemini comparison is infeasible with real data —
comparing only what's actually real: gemini-3.1-flash-lite (tier=cheap),
gemini-3-flash-preview (tier=strong), and qwen2.5:7b via Ollama (no
LiteLLM route has it as primary — always the last fallback hop — so it's
called directly, reusing the exact same retrieval + build_qa_prompt()
output the Gemini paths use, for a fair comparison).

Usage: python scripts/run_experiment_model_provider.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.dataops.vietnamese_normalizer import normalize_for_search  # noqa: E402
from src.evaluation import golden_set  # noqa: E402
from src.evaluation import metrics as em  # noqa: E402
from src.evaluation.judge import GeminiJudge, JudgeCache  # noqa: E402
from src.evaluation.runner import run_question  # noqa: E402
from src.rag.citation import parse_model_output  # noqa: E402
from src.rag.gateway_client import GatewayError  # noqa: E402
from src.rag.litellm_gateway import LiteLLMGateway  # noqa: E402
from src.rag.prompt_builder import RegistryPromptProvider, build_qa_prompt  # noqa: E402
from src.rag.service import RagService  # noqa: E402
from src.retrieval import metrics as rm  # noqa: E402
from src.retrieval.citation_matcher import group_chunks_by_document, match_question  # noqa: E402
from src.retrieval.retriever import retrieve  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"
OUT_PATH = PROJECT_ROOT / "docs" / "system" / "experiments" / "results_model_provider_comparison.md"
N = 10
JUDGE_CALL_DELAY = 6.5
OLLAMA_MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"


def _load_manifest() -> dict:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def _gateway() -> LiteLLMGateway:
    settings = get_settings()
    return LiteLLMGateway(base_url=settings.litellm_base_url, master_key=settings.litellm_master_key)


def _run_gemini_direct_route(
    model_route: str, service: RagService, judge: GeminiJudge, item: dict, chunks_by_doc, chunk_text_by_id,
    eval_k: int, litellm_base_url: str, litellm_master_key: str,
) -> dict[str, Any]:
    """Call a specific LiteLLM model_list entry directly (e.g.
    "strong-tertiary") instead of the tier-based "{tier}-primary" name that
    LiteLLMGateway.generate() always uses — bypasses that tier's automatic
    primary->secondary fallback chain to reach a SPECIFIC key/model
    combination on purpose. Used when the tier's primary key is
    quota-exhausted (confirmed live: `tier="strong"` kept landing on
    secondary/gemini-3.1-flash-lite even on a fresh isolated call) but a
    different key for the SAME real model (gemini-3-flash-preview via
    KEY_5, litellm_config.yaml's strong-tertiary route) still has quota."""
    dense_q = service._embed_fn(item["question"])  # noqa: SLF001
    norm_query = normalize_for_search(item["question"])
    sparse_q = service._bm25.vectorize_query(norm_query)  # noqa: SLF001
    chunks = retrieve(service._client, service._collection, service._ret_cfg, dense_q, sparse_q)  # noqa: SLF001

    prompt = build_qa_prompt(item["question"], chunks, service._prompt.template)  # noqa: SLF001
    t0 = time.perf_counter()
    resp = httpx.post(
        f"{litellm_base_url}/chat/completions",
        json={"model": model_route, "messages": [{"role": "user", "content": prompt}],
              "response_format": {"type": "json_object"}},
        headers={"Authorization": f"Bearer {litellm_master_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    text = data["choices"][0]["message"]["content"]
    generation_ms = int((time.perf_counter() - t0) * 1000)
    cost_usd = float(resp.headers.get("x-litellm-response-cost", 0.0))

    parsed = parse_model_output(text, chunks, require_citation=True)

    groups = [set(m.chunk_ids) for m in match_question(item, chunks_by_doc)]
    groups = [g for g in groups if g]
    retrieved_ids = [c["chunk_id"] for c in chunks]
    ret_eval = rm.evaluate_question(retrieved_ids, groups, k=eval_k) if groups else None
    cited_ids = [c.chunk_id for c in parsed.citations]
    cit_acc = em.citation_accuracy(cited_ids, groups) if not parsed.refusal else None

    judge_result = None
    if not parsed.refusal:
        context_text = "\n\n".join(chunk_text_by_id.get(cid, "") for cid in retrieved_ids)
        try:
            score = judge.score(item["question"], parsed.answer, context_text, item.get("ground_truth", ""))
            judge_result = {
                "faithfulness": score.faithfulness, "answer_relevance": score.answer_relevance,
                "context_relevance": score.context_relevance, "hallucination": score.hallucination,
            }
            if not score.from_cache:
                time.sleep(JUDGE_CALL_DELAY)
        except GatewayError as exc:
            judge_result = {"error": str(exc)[:200]}

    return {
        "question_id": item["id"], "category": item["category"], "got_refusal": parsed.refusal,
        "refusal_correct": parsed.refusal == item["requires_refusal"], "retrieval_eval": ret_eval,
        "citation_accuracy": cit_acc, "judge": judge_result, "latency_ms": generation_ms,
        "cost_usd": cost_usd, "fallback_hop": "primary", "error_labels": [],
    }


def _run_ollama_question(
    service: RagService, judge: GeminiJudge, item: dict, chunks_by_doc, chunk_text_by_id, eval_k: int
) -> dict[str, Any]:
    """Manual replica of src/evaluation/runner.py::run_question()'s logic,
    swapping the generation call for a direct Ollama HTTP call — same
    retrieval + build_qa_prompt() output the Gemini paths use."""
    dense_q = service._embed_fn(item["question"])  # noqa: SLF001 - one-off experiment script
    norm_query = normalize_for_search(item["question"])
    sparse_q = service._bm25.vectorize_query(norm_query)  # noqa: SLF001
    chunks = retrieve(service._client, service._collection, service._ret_cfg, dense_q, sparse_q)  # noqa: SLF001

    prompt = build_qa_prompt(item["question"], chunks, service._prompt.template)  # noqa: SLF001
    t0 = time.perf_counter()
    resp = httpx.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"num_ctx": 4096},
            "stream": False,
            # LiteLLM's `response_format={"type":"json_object"}` (the JSON
            # mode production always requests, litellm_gateway.py:70) maps
            # to Ollama's native `format: "json"` for the ollama_chat
            # provider — production fallback traffic already gets this.
            # Without it, qwen2.5:7b emits raw unescaped newlines inside
            # JSON string values (confirmed by a smoke-test call missing
            # this flag: valid-looking JSON that fails strict json.loads,
            # falling into citation.py's fail-closed refusal) — NOT setting
            # this would make the local-model comparison unfairly worse
            # than what production actually experiences.
            "format": "json",
        },
        timeout=120,
    )
    resp.raise_for_status()
    text = resp.json()["message"]["content"]
    generation_ms = int((time.perf_counter() - t0) * 1000)

    parsed = parse_model_output(text, chunks, require_citation=True)

    groups = [set(m.chunk_ids) for m in match_question(item, chunks_by_doc)]
    groups = [g for g in groups if g]
    retrieved_ids = [c["chunk_id"] for c in chunks]
    ret_eval = rm.evaluate_question(retrieved_ids, groups, k=eval_k) if groups else None
    cited_ids = [c.chunk_id for c in parsed.citations]
    cit_acc = em.citation_accuracy(cited_ids, groups) if not parsed.refusal else None

    judge_result = None
    if not parsed.refusal:
        context_text = "\n\n".join(chunk_text_by_id.get(cid, "") for cid in retrieved_ids)
        try:
            score = judge.score(item["question"], parsed.answer, context_text, item.get("ground_truth", ""))
            judge_result = {
                "faithfulness": score.faithfulness, "answer_relevance": score.answer_relevance,
                "context_relevance": score.context_relevance, "hallucination": score.hallucination,
            }
            if not score.from_cache:
                time.sleep(JUDGE_CALL_DELAY)
        except GatewayError as exc:
            judge_result = {"error": str(exc)[:200]}

    return {
        "question_id": item["id"], "category": item["category"], "got_refusal": parsed.refusal,
        "refusal_correct": parsed.refusal == item["requires_refusal"], "retrieval_eval": ret_eval,
        "citation_accuracy": cit_acc, "judge": judge_result, "latency_ms": generation_ms,
        "cost_usd": 0.0, "fallback_hop": "primary", "error_labels": [],
    }


def _to_dict(r: Any) -> dict[str, Any]:
    """QuestionResult dataclass (Gemini path) or plain dict (Ollama path) -> plain dict."""
    if isinstance(r, dict):
        return r
    return {
        "question_id": r.question_id, "category": r.category, "got_refusal": r.got_refusal,
        "refusal_correct": r.refusal_correct, "retrieval_eval": r.retrieval_eval,
        "citation_accuracy": r.citation_accuracy, "judge": r.judge, "latency_ms": r.latency_ms,
        "cost_usd": r.cost_usd, "fallback_hop": r.fallback_hop,
    }


def _aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    judged = [r["judge"] for r in results if r.get("judge") and "error" not in r["judge"]]
    cit_accs = [r["citation_accuracy"] for r in results if r.get("citation_accuracy") is not None]
    latencies = sorted(r["latency_ms"] for r in results if r.get("latency_ms"))
    p95 = latencies[int(len(latencies) * 0.95) - 1] if latencies else None
    non_primary = sum(1 for r in results if r.get("fallback_hop") not in ("primary", "n/a", None))
    return {
        "n": n,
        "refusal_accuracy": sum(1 for r in results if r["refusal_correct"]) / n if n else None,
        "citation_accuracy": sum(cit_accs) / len(cit_accs) if cit_accs else None,
        "faithfulness": sum(j["faithfulness"] for j in judged) / len(judged) if judged else None,
        "hallucination_rate": sum(1.0 if j["hallucination"] else 0.0 for j in judged) / len(judged) if judged else None,
        "avg_cost_usd": sum(r["cost_usd"] for r in results) / n if n else None,
        "p95_latency_ms": p95,
        "non_primary_rate": non_primary / n if n else None,
        "n_judged": len(judged),
    }


def main() -> None:
    settings = get_settings()
    manifest = _load_manifest()
    chunks_path = CHUNKS_DIR / f"{manifest['chunking_strategy_indexed']}_{manifest['data_version']}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    chunks_by_doc = group_chunks_by_document(chunks)
    chunk_text_by_id = {c["chunk_id"]: c["text"] for c in chunks}

    items = golden_set.smoke_subset(golden_set.load_all(), size=N, seed=8)
    print(f"Selected {len(items)} questions (n={N}, seed=8)")

    service = RagService(
        gateway=_gateway(), qdrant_url=settings.qdrant_url,
        prompt_provider=RegistryPromptProvider(settings.postgres_dsn),
    )
    eval_k = service.context_limit
    judge = GeminiJudge(_gateway(), JudgeCache(EVAL_DIR / f"judge_cache_model_provider_{manifest['data_version']}.json"))

    all_results: dict[str, list[dict]] = {"gemini-3.1-flash-lite (cheap)": [], "gemini-3-flash-preview (strong)": [], "qwen2.5:7b (Ollama, local)": []}

    print("\n=== gemini-3.1-flash-lite (tier=cheap) ===")
    for i, item in enumerate(items, start=1):
        print(f"  [{i}/{N}] {item['id']} ...", end=" ", flush=True)
        try:
            r = run_question(service, judge, item, chunks_by_doc, chunk_text_by_id, eval_k=eval_k, mode="cheap")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")
            continue
        all_results["gemini-3.1-flash-lite (cheap)"].append(_to_dict(r))
        print(f"refusal={r.got_refusal} fallback={r.fallback_hop}")

    print("\n=== gemini-3-flash-preview (tier=strong) ===")
    for i, item in enumerate(items, start=1):
        print(f"  [{i}/{N}] {item['id']} ...", end=" ", flush=True)
        try:
            r = run_question(service, judge, item, chunks_by_doc, chunk_text_by_id, eval_k=eval_k, mode="strong")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")
            continue
        all_results["gemini-3-flash-preview (strong)"].append(_to_dict(r))
        print(f"refusal={r.got_refusal} fallback={r.fallback_hop}")

    print("\n=== qwen2.5:7b (Ollama, local, direct HTTP) ===")
    for i, item in enumerate(items, start=1):
        print(f"  [{i}/{N}] {item['id']} ...", end=" ", flush=True)
        try:
            r = _run_ollama_question(service, judge, item, chunks_by_doc, chunk_text_by_id, eval_k)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")
            continue
        all_results["qwen2.5:7b (Ollama, local)"].append(r)
        print(f"refusal={r['got_refusal']}")

    # Filter Gemini results to fallback_hop=="primary" only, so a same-day
    # quota hiccup doesn't get misattributed to the wrong model's quality.
    for key in ("gemini-3.1-flash-lite (cheap)", "gemini-3-flash-preview (strong)"):
        before = len(all_results[key])
        all_results[key] = [r for r in all_results[key] if r["fallback_hop"] == "primary"]
        dropped = before - len(all_results[key])
        if dropped:
            print(f"\n{key}: dropped {dropped}/{before} non-primary-hop results from aggregation")

    lines = [
        "# Experiment 3 (part 2) — Model/Provider Comparison",
        "",
        "**Ràng buộc thật**: dự án CHƯA BAO GIỜ có key OpenAI/Anthropic "
        "(`config/model_gateway.yaml`'s header comment ghi rõ từ Phase 5) — "
        "so sánh GPT-5/Claude/Gemini theo blueprint gốc KHÔNG khả thi với dữ "
        "liệu thật. So sánh đúng những gì thật sự có: 2 model Gemini (khác "
        "tier, khác tốc độ/chất lượng) + 1 model local qua Ollama (không có "
        "route LiteLLM nào coi Ollama là primary — luôn là fallback cuối — "
        "nên gọi trực tiếp HTTP, dùng ĐÚNG retrieval + `build_qa_prompt()` "
        "các model Gemini dùng để so sánh công bằng).",
        "",
        f"n={N} câu (stratified, seed=8), prompt_version=`{service._prompt.version}` "  # noqa: SLF001
        f"(production hiện tại). Kết quả Gemini đã lọc chỉ giữ "
        "`fallback_hop=primary` (loại quota hiccup cùng ngày khỏi phép so sánh).",
        "",
        "| Model | n | Citation Acc | Faithfulness | Hallucination | Refusal Acc | p95 latency (ms) | Avg cost/req | Non-primary rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, results in all_results.items():
        if not results:
            lines.append(f"| {name} | 0 | — | — | — | — | — | — | — |")
            continue
        agg = _aggregate(results)
        lines.append(
            f"| {name} | {agg['n']} | {agg['citation_accuracy']} | {agg['faithfulness']} | "
            f"{agg['hallucination_rate']} | {agg['refusal_accuracy']} | {agg['p95_latency_ms']} | "
            f"{agg['avg_cost_usd']} | {agg['non_primary_rate']} |"
        )

    OUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
