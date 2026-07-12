"""Golden set loader for the Evaluation Engine (Phase 8, Module 5).

Reuses the same JSONL contract Phase 2/4 established
(data/test_sets/golden_set.jsonl) and adds mode-based subset selection so
CI can run a cheap `smoke` slice while `full` exercises every question
before a milestone (modules/05_evaluation_engine.md).
"""

from __future__ import annotations

import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_SET_PATH = PROJECT_ROOT / "data" / "test_sets" / "golden_set.jsonl"

SMOKE_SEED = 8
SMOKE_SIZE = 50


def load_all(path: Path | None = None) -> list[dict]:
    p = path or GOLDEN_SET_PATH
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def smoke_subset(items: list[dict], size: int = SMOKE_SIZE, seed: int = SMOKE_SEED) -> list[dict]:
    """Stratified sample: each category's share of `size` is proportional to
    its share of the full set, so a 50-question smoke run still touches
    every category instead of only the 218-strong factoid bucket. Sampling
    within each category is seeded for reproducibility across CI runs."""
    by_cat: dict[str, list[dict]] = {}
    for it in items:
        by_cat.setdefault(it["category"], []).append(it)

    rng = random.Random(seed)
    quota = {cat: max(1, round(len(v) / len(items) * size)) for cat, v in by_cat.items()}

    picked: list[dict] = []
    for cat, pool in by_cat.items():
        pool_sorted = sorted(pool, key=lambda x: x["id"])
        rng.shuffle(pool_sorted)
        picked.extend(pool_sorted[: quota[cat]])

    picked.sort(key=lambda x: x["id"])
    return picked[:size]


def select(mode: str, category: str | None = None, path: Path | None = None) -> list[dict]:
    items = load_all(path)
    if mode == "full":
        return items
    if mode == "smoke":
        return smoke_subset(items)
    if mode == "targeted":
        if not category:
            raise ValueError("mode=targeted requires a category")
        chosen = [i for i in items if i["category"] == category]
        if not chosen:
            raise ValueError(f"no questions with category={category!r}")
        return chosen
    raise ValueError(f"unknown mode: {mode!r}")
