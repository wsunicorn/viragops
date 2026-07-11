"""Offline prompt comparison on a smoke subset (Phase 6, Module 4).

Runs every `testing`/`active` version of prompt `rag_qa_vi` against a
small golden-set smoke slice (default 12 questions: answerable + refusal
+ adversarial), through the REAL retrieval index and REAL gateway, and
scores what is measurable WITHOUT an LLM judge (that's Phase 8):

- parse_ok            — output tuân JSON contract
- refusal_correct     — đúng kỳ vọng requires_refusal của golden set
- citation_valid      — câu trả lời (không refusal) có >=1 citation hợp lệ
- grounded_citation   — >=1 citation trúng relevant_chunks của golden set
- avg output tokens, avg generation latency

Retrieval runs ONCE per question and is shared across all prompt
versions (retrieval is prompt-independent); query embeddings come from
the Phase 4 cache — the only quota spent is ~n_prompts × n_questions
generation calls on the cheap/balanced tier.

Each tested version gets `eval_result_id = <comparison run id>` written
back to the registry, unlocking data-driven activation (registry policy).

Usage:
    python scripts/run_prompt_comparison.py            # 12 câu mặc định
    python scripts/run_prompt_comparison.py --limit 6  # thử nhanh
    python scripts/run_prompt_comparison.py --activate-best
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.dataops.sparse_bm25 import BM25Sparse  # noqa: E402
from src.promptops.registry import PromptRegistry  # noqa: E402
from src.rag.citation import parse_model_output  # noqa: E402
from src.rag.gateway_client import GeminiGateway  # noqa: E402
from src.rag.prompt_builder import build_qa_prompt  # noqa: E402
from src.retrieval.citation_matcher import group_chunks_by_document, match_question  # noqa: E402
from src.retrieval.retriever import RetrievalConfig, retrieve  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EXPERIMENTS_DIR = PROJECT_ROOT / "data" / "experiments"
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
RESULTS_DOC = PROJECT_ROOT / "docs" / "system" / "experiments" / "results_prompt_comparison.md"

PROMPT_ID = "rag_qa_vi"
GEN_DELAY_SECONDS = 6.5  # flash-lite ~10 RPM (config/model_gateway.yaml)

# Smoke slice cố định (tái lập được): 8 câu có đáp án phủ nhiều chủ đề/độ khó
# + 2 refusal thật + 2 adversarial (prompt injection) từ golden set.
SMOKE_QUESTION_IDS = [
    "q_001", "q_010", "q_022", "q_030", "q_041", "q_055", "q_063", "q_070",  # answerable
    "q_051", "q_052",                                                        # out_of_scope refusal
    "q_053", "q_054",                                                        # adversarial
]


def load_smoke_questions(limit: int | None) -> list[dict]:
    rows = {  # id -> item
        r["id"]: r
        for r in (json.loads(x) for x in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines() if x.strip())
    }
    missing = [qid for qid in SMOKE_QUESTION_IDS if qid not in rows]
    if missing:
        raise SystemExit(f"smoke ids not in golden set: {missing}")
    picked = [rows[qid] for qid in SMOKE_QUESTION_IDS]
    return picked[:limit] if limit else picked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="số câu (mặc định 12)")
    parser.add_argument("--activate-best", action="store_true",
                        help="activate version thắng cuộc sau khi chạy")
    args = parser.parse_args()

    run_id = f"promptcmp_{datetime.now(UTC).strftime('%Y%m%d_%H%M')}"
    questions = load_smoke_questions(args.limit)

    registry = PromptRegistry(get_settings().postgres_dsn)
    versions = [
        registry.get(PROMPT_ID, v["prompt_version"])
        for v in registry.list_versions(PROMPT_ID)
        if v["status"] in ("testing", "active")
    ]
    print(f"{run_id}: {len(versions)} prompt versions x {len(questions)} questions")

    # --- shared retrieval (prompt-independent) ---------------------------
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    manifest = json.loads(manifests[-1].read_text(encoding="utf-8"))
    data_version = manifest["data_version"]
    rcfg = yaml.safe_load((PROJECT_ROOT / "config" / "retrieval.yaml").read_text(encoding="utf-8"))
    fusion = rcfg["retrieval"]["fusion"]["method"]
    ret_cfg = RetrievalConfig(
        config_id=rcfg["retrieval_config_id"],
        mode=f"hybrid_{fusion}",
        top_k_before=rcfg["retrieval"]["dense"]["top_k"],
        limit=rcfg["reranker"]["top_k_after"],
    )

    emb_cache_path = EXPERIMENTS_DIR / f"query_embeddings_{data_version}.json"
    emb_cache_full = json.loads(emb_cache_path.read_text(encoding="utf-8"))
    emb_cache = emb_cache_full["vectors"]

    # Phase 4 chỉ cache 71 câu non-refusal; smoke set có thêm câu refusal/
    # adversarial -> embed bổ sung phần thiếu (vài item, có key-rotation).
    missing_qs = [q for q in questions if q["id"] not in emb_cache]
    if missing_qs:
        from src.dataops import embedder

        print(f"embedding {len(missing_qs)} smoke queries missing from cache")
        vecs = embedder.embed_batch(
            [q["question"] for q in missing_qs],
            model=emb_cache_full["model"],
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=emb_cache_full["dim"],
        )
        for q, v in zip(missing_qs, vecs, strict=True):
            emb_cache[q["id"]] = v
        emb_cache_path.write_text(json.dumps(emb_cache_full), encoding="utf-8")
    state_path = CHUNKS_DIR / f"bm25_state_structure_aware_{data_version}.json"
    bm25 = BM25Sparse.from_state(json.loads(state_path.read_text(encoding="utf-8")))

    from qdrant_client import QdrantClient

    client = QdrantClient(url=get_settings().qdrant_url)

    chunks_all = [
        json.loads(x)
        for x in (CHUNKS_DIR / f"structure_aware_{data_version}.jsonl").read_text(encoding="utf-8").splitlines()
        if x.strip()
    ]
    by_doc = group_chunks_by_document(chunks_all)

    retrieved_by_q: dict[str, list[dict]] = {}
    relevant_by_q: dict[str, set[str]] = {}
    for q in questions:
        retrieved_by_q[q["id"]] = retrieve(
            client, manifest["qdrant_collection"], ret_cfg,
            emb_cache[q["id"]], bm25.vectorize_query(q["question"]),
        )
        relevant_by_q[q["id"]] = {
            cid for m in match_question(q, by_doc) for cid in m.chunk_ids
        }

    # --- run each prompt version -----------------------------------------
    gateway = GeminiGateway()
    rows = []
    for pv in versions:
        stats = {
            "parse_ok": 0, "refusal_correct": 0, "n_refusal_expected": 0,
            "citation_valid": 0, "grounded": 0, "n_answerable": 0,
            "tokens": [], "latencies": [],
        }
        print(f"\n[{pv.prompt_version}]")
        for q in questions:
            chunks = retrieved_by_q[q["id"]]
            prompt = build_qa_prompt(q["question"], chunks, pv.template)
            gen = gateway.generate(tier=pv.model_tier, prompt=prompt)
            parsed = parse_model_output(gen.text, chunks)

            stats["tokens"].append(gen.output_tokens)
            stats["latencies"].append(gen.latency_ms)
            if parsed.parse_error != "unparseable_model_output":
                stats["parse_ok"] += 1

            if q["requires_refusal"]:
                stats["n_refusal_expected"] += 1
                if parsed.refusal:
                    stats["refusal_correct"] += 1
            else:
                stats["n_answerable"] += 1
                if not parsed.refusal and parsed.citations:
                    stats["citation_valid"] += 1
                    if any(c.chunk_id in relevant_by_q[q["id"]] for c in parsed.citations):
                        stats["grounded"] += 1
            time.sleep(GEN_DELAY_SECONDS)

        n = len(questions)
        row = {
            "prompt_version": pv.prompt_version,
            "parse_ok_rate": stats["parse_ok"] / n,
            "refusal_accuracy": (
                stats["refusal_correct"] / stats["n_refusal_expected"]
                if stats["n_refusal_expected"] else None
            ),
            "citation_valid_rate": (
                stats["citation_valid"] / stats["n_answerable"] if stats["n_answerable"] else None
            ),
            "grounded_citation_rate": (
                stats["grounded"] / stats["n_answerable"] if stats["n_answerable"] else None
            ),
            "avg_output_tokens": round(statistics.mean(stats["tokens"]), 1),
            "avg_gen_ms": round(statistics.mean(stats["latencies"]), 0),
        }
        rows.append(row)
        print(f"  parse={row['parse_ok_rate']:.2f} refusal={row['refusal_accuracy']} "
              f"cite={row['citation_valid_rate']} grounded={row['grounded_citation_rate']} "
              f"tokens={row['avg_output_tokens']}")
        registry.set_eval_result(PROMPT_ID, pv.prompt_version, run_id)

    # --- pick best + report ----------------------------------------------
    def score(r: dict) -> tuple:
        return (
            (r["refusal_accuracy"] or 0) + (r["grounded_citation_rate"] or 0),
            (r["citation_valid_rate"] or 0),
            -r["avg_output_tokens"],
        )

    best = max(rows, key=score)

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = EXPERIMENTS_DIR / f"{run_id}.csv"
    cols = list(rows[0].keys())
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    lines = [
        "# Kết quả so sánh prompt P0-P5 (smoke set)",
        "",
        f"> Run `{run_id}` — {len(questions)} câu smoke ({len(SMOKE_QUESTION_IDS)} id cố định trong "
        "`scripts/run_prompt_comparison.py`), retrieval dùng chung "
        f"(`{rcfg['retrieval_config_id']}`), gateway tier theo từng prompt (balanced). "
        "Metric đo được KHÔNG cần LLM-judge; faithfulness/answer-relevance đầy đủ chờ "
        "Evaluation Engine (Phase 8).",
        "",
        "| version | parse ok | refusal acc | citation valid | grounded cite | avg tokens | avg gen ms |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(rows, key=score, reverse=True):
        mark = " **(best)**" if r["prompt_version"] == best["prompt_version"] else ""
        fmt = lambda v: "—" if v is None else f"{v:.2f}"  # noqa: E731
        lines.append(
            f"| {r['prompt_version']}{mark} | {fmt(r['parse_ok_rate'])} | {fmt(r['refusal_accuracy'])} | "
            f"{fmt(r['citation_valid_rate'])} | {fmt(r['grounded_citation_rate'])} | "
            f"{r['avg_output_tokens']} | {r['avg_gen_ms']:.0f} |"
        )
    lines += [
        "",
        f"- Best (refusal+grounded, tie-break ít token): **{best['prompt_version']}**.",
        f"- Mọi version đã được gán `eval_result_id={run_id}` trong registry.",
        f"- CSV: `data/experiments/{csv_path.name}`.",
    ]
    RESULTS_DOC.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nreport -> {RESULTS_DOC.relative_to(PROJECT_ROOT)}")
    print(f"best: {best['prompt_version']}")

    if args.activate_best:
        registry.activate(PROMPT_ID, best["prompt_version"], actor=f"run_prompt_comparison:{run_id}")
        print(f"activated {best['prompt_version']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
