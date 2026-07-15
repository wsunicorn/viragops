"""Trade-off charts (Phase 12) — visualizes numbers ALREADY published in
real experiment reports (no new measurement here, just rendering). No
chart-generation script existed anywhere in this repo before (the 11
existing docs/figures/*.png were all made externally/manually) — matplotlib
added as a new optional dep (pyproject.toml `reporting` group) for this.

Sources (values copied verbatim, cited inline):
- docs/system/experiments/results_retrieval_reranking.md (Exp 1/2, 249 câu,
  hybrid_dbsf_pre40 best config)
- docs/system/experiments/results_optimization_o1_o8.md (Exp 6, n=15,
  O2_pass2/O7 faithfulness excluded — documented judge/cache artifact,
  see that report's own caveat block)

Usage: python scripts/generate_tradeoff_charts.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_ROOT / "docs" / "figures"

# --- Chart 1: retrieval config comparison (results_retrieval_reranking.md) ---
RETRIEVAL_CONFIGS = ["dense_top5", "sparse_bm25_top5", "hybrid_rrf_pre40", "hybrid_dbsf_pre40"]
RETRIEVAL_METRICS = {
    "recall@5": [0.882, 0.865, 0.906, 0.932],
    "MRR": [0.657, 0.708, 0.761, 0.791],
    "nDCG@5": [0.699, 0.734, 0.785, 0.815],
}

# --- Chart 2: O1-O8 optimization trade-off (results_optimization_o1_o8.md) ---
# faithfulness=None cho O2_pass2/O7 (artefact judge chấm context rỗng khi
# cache hit — xem caveat trong report gốc, KHÔNG dùng số này).
O_CONFIGS = ["O1_baseline", "O2_cache_cold", "O3_compression", "O4_dynamic_topk", "O5_routing", "O7_combined"]
O_COST_USD = [0.000911, 0.000918, 0.000714, 0.000850, 0.000912, 0.0]
O_P95_LATENCY_MS = [1520, 1629, 1409, 1638, 2093, None]
O_CITATION_ACC = [0.792, 0.778, 0.850, 0.792, 0.778, 0.778]


def chart_retrieval_comparison() -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(RETRIEVAL_CONFIGS))
    width = 0.25
    for i, (metric, values) in enumerate(RETRIEVAL_METRICS.items()):
        offset = (i - 1) * width
        ax.bar([xi + offset for xi in x], values, width, label=metric)
    ax.set_xticks(list(x))
    ax.set_xticklabels(RETRIEVAL_CONFIGS, rotation=15, ha="right")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.0)
    ax.set_title("Retrieval config comparison (249 câu, k=5)\nresults_retrieval_reranking.md")
    ax.legend()
    ax.axhline(0.85, color="red", linestyle="--", linewidth=0.8, label="recall target 0.85")
    fig.tight_layout()
    out = FIG_DIR / "fig_retrieval_comparison_real.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def chart_optimization_tradeoff() -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    axes[0].bar(O_CONFIGS, O_COST_USD, color="#2a9d8f")
    axes[0].set_title("Avg cost/request (USD)")
    axes[0].tick_params(axis="x", rotation=35)

    lat_x = [c for c, v in zip(O_CONFIGS, O_P95_LATENCY_MS, strict=True) if v is not None]
    lat_y = [v for v in O_P95_LATENCY_MS if v is not None]
    axes[1].bar(lat_x, lat_y, color="#e76f51")
    axes[1].set_title("p95 latency (ms)\n(O7 = cache hit, ~0ms, không hiển thị)")
    axes[1].tick_params(axis="x", rotation=35)

    axes[2].bar(O_CONFIGS, O_CITATION_ACC, color="#264653")
    axes[2].axhline(0.85, color="red", linestyle="--", linewidth=0.8)
    axes[2].set_title("Citation accuracy\n(target 0.85, đường đỏ)")
    axes[2].set_ylim(0, 1.0)
    axes[2].tick_params(axis="x", rotation=35)

    fig.suptitle("O1-O8 Optimization trade-off (n=15, results_optimization_o1_o8.md)")
    fig.tight_layout()
    out = FIG_DIR / "fig_o1_o8_tradeoff_real.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    p1 = chart_retrieval_comparison()
    p2 = chart_optimization_tradeoff()
    print(f"wrote {p1}")
    print(f"wrote {p2}")


if __name__ == "__main__":
    main()
