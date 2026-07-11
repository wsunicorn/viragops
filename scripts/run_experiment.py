"""Retrieval experiment runner — Phase 4 (Module 2, Experiment 1 & 2).

Runs every config of one experiment from config/experiments_retrieval.yaml
against the golden set's 71 non-refusal questions, scores with
citation-coverage metrics (src/retrieval/metrics.py — relevance derived
from expected_citations via src/retrieval/citation_matcher.py, recomputed
per chunking strategy so each strategy is judged at its own granularity),
and writes:

- CSV of per-config aggregates -> data/experiments/<experiment>_<ts>.csv
- Markdown report (incl. failure analysis for the best config)
  -> docs/system/experiments/results_<experiment>.md

Query embeddings are cached in data/experiments/query_embeddings_*.json —
71 questions cost ONE Gemini batch call total, reused across every
config/strategy/run. Latency reported is retrieval(+rerank) only; query
embedding is excluded since it's cached (noted in the report).

Usage:
    python scripts/run_experiment.py --experiment retrieval_reranking
    python scripts/run_experiment.py --experiment chunking_ablation
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
from qdrant_client import QdrantClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.dataops import embedder  # noqa: E402
from src.dataops.sparse_bm25 import BM25Sparse  # noqa: E402
from src.retrieval import metrics as m  # noqa: E402
from src.retrieval.citation_matcher import group_chunks_by_document, match_question  # noqa: E402
from src.retrieval.reranker import GeminiListwiseReranker  # noqa: E402
from src.retrieval.retriever import RetrievalConfig, retrieve  # noqa: E402

CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
EXPERIMENTS_DIR = PROJECT_ROOT / "data" / "experiments"
RESULTS_DOC_DIR = PROJECT_ROOT / "docs" / "system" / "experiments"
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"
EXPERIMENT_CONFIG = PROJECT_ROOT / "config" / "experiments_retrieval.yaml"
INGEST_CONFIG = PROJECT_ROOT / "config" / "ingest.yaml"
GATEWAY_CONFIG = PROJECT_ROOT / "config" / "model_gateway.yaml"

RERANK_CALL_DELAY = 6.5  # giây — flash-lite free tier ~10 RPM (model_gateway.yaml)


def load_manifest() -> dict:
    manifests = sorted(CHUNKS_DIR.glob("manifest_data_*.json"))
    if not manifests:
        raise SystemExit("No ingest manifest — run scripts/ingest_data.py first")
    return json.loads(manifests[-1].read_text(encoding="utf-8"))


def load_questions() -> list[dict]:
    rows = [json.loads(x) for x in GOLDEN_SET_PATH.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r for r in rows if not r["requires_refusal"]]


def load_query_embeddings(questions: list[dict], manifest: dict) -> dict[str, list[float]]:
    ingest_cfg = yaml.safe_load(INGEST_CONFIG.read_text(encoding="utf-8"))
    dense_cfg = ingest_cfg["embedding"]["dense"]
    model = manifest["embedding_model"]
    dim = dense_cfg["output_dimensionality"]

    cache_path = EXPERIMENTS_DIR / f"query_embeddings_{manifest['data_version']}.json"
    cache: dict = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        if cache.get("model") != model or cache.get("dim") != dim:
            cache = {}

    vectors: dict[str, list[float]] = dict(cache.get("vectors", {}))
    missing = [q for q in questions if q["id"] not in vectors]
    if missing:
        print(f"Embedding {len(missing)} queries (cached: {len(vectors)})")
        new_vecs = embedder.embed_all(
            [q["question"] for q in missing],
            model=model,
            task_type=dense_cfg["task_type_query"],
            output_dimensionality=dim,
            batch_size=dense_cfg["batch_size"],
            batch_delay_seconds=dense_cfg["batch_delay_seconds"],
            progress_label="query-embed",
        )
        for q, vec in zip(missing, new_vecs, strict=True):
            vectors[q["id"]] = vec
        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps({"model": model, "dim": dim, "vectors": vectors}), encoding="utf-8"
        )
    return vectors


def strategy_assets(strategy: str, manifest: dict, ingest_cfg: dict) -> tuple[str, BM25Sparse, dict]:
    """(collection_name, fitted BM25, citation_groups per question id)."""
    data_version = manifest["data_version"]
    if strategy == manifest["chunking_strategy_indexed"]:
        collection = manifest["qdrant_collection"]
    else:
        collection = (
            f"{ingest_cfg['qdrant']['collection_prefix']}_{manifest['index_version']}_{strategy}"
        )

    state_path = CHUNKS_DIR / f"bm25_state_{strategy}_{data_version}.json"
    if not state_path.exists() and strategy == manifest["chunking_strategy_indexed"]:
        state_path = CHUNKS_DIR / f"bm25_state_{data_version}.json"  # tên cũ từ Phase 3
    bm25 = BM25Sparse.from_state(json.loads(state_path.read_text(encoding="utf-8")))

    chunks_path = CHUNKS_DIR / f"{strategy}_{data_version}.jsonl"
    chunks = [json.loads(x) for x in chunks_path.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_doc = group_chunks_by_document(chunks)
    return collection, bm25, by_doc


def run_config(
    client: QdrantClient,
    collection: str,
    cfg_dict: dict,
    questions: list[dict],
    query_vectors: dict[str, list[float]],
    bm25: BM25Sparse,
    chunks_by_doc: dict,
    eval_k: int,
    reranker: GeminiListwiseReranker | None,
) -> tuple[dict, list[dict]]:
    config = RetrievalConfig(
        config_id=cfg_dict["config_id"],
        mode=cfg_dict["mode"],
        top_k_before=cfg_dict.get("top_k_before", 20),
        limit=cfg_dict.get("limit", 5),
        rerank=cfg_dict.get("rerank", "none"),
    )
    rerank_pool = cfg_dict.get("rerank_pool", 10)
    use_rerank = config.rerank == "gemini_listwise"
    if use_rerank and reranker is None:
        raise SystemExit(f"{config.config_id}: rerank requested but reranker unavailable")

    evals: list[m.QuestionEval] = []
    latencies: list[float] = []
    failures: list[dict] = []

    for q in questions:
        groups = [set(match.chunk_ids) for match in match_question(q, chunks_by_doc)]
        if not any(groups):
            continue

        dense_q = query_vectors[q["id"]]
        sparse_q = bm25.vectorize_query(q["question"])

        t0 = time.perf_counter()
        results = retrieve(
            client, collection, config, dense_q, sparse_q,
            fetch_limit=rerank_pool if use_rerank else None,
        )
        if use_rerank:
            results = reranker.rerank(q["question"], results)[: config.limit]
        latencies.append((time.perf_counter() - t0) * 1000)
        if use_rerank:
            time.sleep(RERANK_CALL_DELAY)

        retrieved_ids = [r["chunk_id"] for r in results]
        ev = m.evaluate_question(retrieved_ids, groups, k=eval_k)
        if ev is None:
            continue
        ev.question_id = q["id"]
        evals.append(ev)

        if ev.hit_at_k == 0:
            failures.append(
                {
                    "question_id": q["id"],
                    "question": q["question"],
                    "expected": [c.get("section", "") for c in q.get("expected_citations", [])],
                    "expected_docs": q.get("relevant_documents", []),
                    "got_top1": (
                        f"{results[0]['document_id']} · {results[0].get('section')}"
                        if results
                        else "(no results)"
                    ),
                }
            )

    agg = m.aggregate(evals)
    agg.update(
        config_id=config.config_id,
        mode=config.mode,
        rerank=config.rerank,
        top_k_before=config.top_k_before,
        latency_p50_ms=round(statistics.median(latencies), 1) if latencies else None,
        latency_p95_ms=(
            round(sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)], 1) if latencies else None
        ),
    )
    return agg, failures


def write_outputs(
    experiment: str, rows: list[dict], failures_best: list[dict], meta: dict, eval_k: int
) -> None:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M")
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    csv_path = EXPERIMENTS_DIR / f"{experiment}_{ts}.csv"
    cols = [
        "config_id", "mode", "rerank", "top_k_before", "n_questions",
        "recall_at_k", "hit_rate", "mrr", "ndcg_at_k", "latency_p50_ms", "latency_p95_ms",
    ]
    with csv_path.open("w", encoding="utf-8") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(c, "")) for c in cols) + "\n")

    best = max(rows, key=lambda r: (r["recall_at_k"], r["ndcg_at_k"]))
    lines = [
        f"# Kết quả experiment: {experiment}",
        "",
        f"> Sinh bởi `scripts/run_experiment.py` lúc {ts} UTC. "
        f"data_version=`{meta['data_version']}`, index_version=`{meta['index_version']}`, "
        f"embedding=`{meta['embedding_model']}`. Metric tính ở k={eval_k} theo "
        "`contracts/metric_definitions.md`; relevance = citation-coverage "
        "(xem docstring `src/retrieval/metrics.py`). Latency chỉ tính retrieval(+rerank), "
        "KHÔNG gồm embed query (đã cache) — p95 API thật ở Phase 5 sẽ cao hơn.",
        "",
        f"| config | mode | rerank | recall@{eval_k} | hit rate | MRR | nDCG@{eval_k} | p50 ms | p95 ms |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in sorted(rows, key=lambda x: -x["recall_at_k"]):
        mark = " **(best)**" if r["config_id"] == best["config_id"] else ""
        lines.append(
            f"| {r['config_id']}{mark} | {r['mode']} | {r['rerank']} | "
            f"{r['recall_at_k']:.3f} | {r['hit_rate']:.3f} | {r['mrr']:.3f} | "
            f"{r['ndcg_at_k']:.3f} | {r['latency_p50_ms']} | {r['latency_p95_ms']} |"
        )

    target = 0.85
    lines += [
        "",
        f"- Best config: **{best['config_id']}** — recall@{eval_k}={best['recall_at_k']:.3f}, "
        f"nDCG@{eval_k}={best['ndcg_at_k']:.3f} "
        f"({'ĐẠT' if best['recall_at_k'] >= target else 'CHƯA ĐẠT'} target recall >= {target} "
        "của metric_definitions.md).",
        f"- Số câu đánh giá: {best['n_questions']} (câu không-refusal có citation khớp được).",
        "",
        f"## Phân tích lỗi — câu hit@{eval_k}=0 với best config ({len(failures_best)} câu)",
        "",
    ]
    if failures_best:
        lines += [
            "| question | hỏi | citation kỳ vọng | top-1 nhận được |",
            "|---|---|---|---|",
        ]
        for fl in failures_best:
            q_short = fl["question"][:70].replace("|", "/")
            exp = "; ".join(fl["expected"])[:70].replace("|", "/")
            lines.append(f"| {fl['question_id']} | {q_short} | {exp} | {fl['got_top1']} |")
    else:
        lines.append("Không có câu nào trượt hoàn toàn ở top-k với best config.")

    doc_path = RESULTS_DOC_DIR / f"results_{experiment}.md"
    doc_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nCSV -> {csv_path.relative_to(PROJECT_ROOT)}")
    print(f"Report -> {doc_path.relative_to(PROJECT_ROOT)}")
    print(f"Best: {best['config_id']} recall@{eval_k}={best['recall_at_k']:.3f}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", required=True, choices=["retrieval_reranking", "chunking_ablation"])
    args = parser.parse_args()

    exp_cfg = yaml.safe_load(EXPERIMENT_CONFIG.read_text(encoding="utf-8"))
    ingest_cfg = yaml.safe_load(INGEST_CONFIG.read_text(encoding="utf-8"))
    manifest = load_manifest()
    eval_k = exp_cfg["eval_k"]

    questions = load_questions()
    query_vectors = load_query_embeddings(questions, manifest)

    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url)

    needs_rerank = args.experiment == "retrieval_reranking" and any(
        c.get("rerank") for c in exp_cfg["retrieval_reranking"]["configs"]
    )
    reranker = (
        GeminiListwiseReranker(str(GATEWAY_CONFIG)) if needs_rerank else None
    )

    rows: list[dict] = []
    failures_by_config: dict[str, list[dict]] = {}

    if args.experiment == "retrieval_reranking":
        strategy = exp_cfg["retrieval_reranking"]["strategy"]
        collection, bm25, by_doc = strategy_assets(strategy, manifest, ingest_cfg)
        for cfg_dict in exp_cfg["retrieval_reranking"]["configs"]:
            print(f"\n[{cfg_dict['config_id']}] running on '{collection}'")
            agg, failures = run_config(
                client, collection, cfg_dict, questions, query_vectors,
                bm25, by_doc, eval_k, reranker,
            )
            print(f"  recall@{eval_k}={agg['recall_at_k']:.3f} mrr={agg['mrr']:.3f}")
            rows.append(agg)
            failures_by_config[cfg_dict["config_id"]] = failures
    else:
        base = exp_cfg["chunking_ablation"]["base_config"]
        for strategy in exp_cfg["chunking_ablation"]["strategies"]:
            collection, bm25, by_doc = strategy_assets(strategy, manifest, ingest_cfg)
            cfg_dict = {**base, "config_id": f"{base['mode']}_{strategy}"}
            print(f"\n[{cfg_dict['config_id']}] running on '{collection}'")
            agg, failures = run_config(
                client, collection, cfg_dict, questions, query_vectors,
                bm25, by_doc, eval_k, None,
            )
            agg["config_id"] = cfg_dict["config_id"]
            print(f"  recall@{eval_k}={agg['recall_at_k']:.3f} mrr={agg['mrr']:.3f}")
            rows.append(agg)
            failures_by_config[cfg_dict["config_id"]] = failures

    best = max(rows, key=lambda r: (r["recall_at_k"], r["ndcg_at_k"]))
    write_outputs(args.experiment, rows, failures_by_config[best["config_id"]], manifest, eval_k)
    return 0


if __name__ == "__main__":
    sys.exit(main())
