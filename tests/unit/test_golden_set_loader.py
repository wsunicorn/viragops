from __future__ import annotations

import pytest

from src.evaluation import golden_set

_CAT_COUNTS = {
    "factoid": 218, "procedural": 12, "multi_hop": 30,
    "out_of_scope": 9, "adversarial": 11, "ambiguous": 20,
}


def _fake_items() -> list[dict]:
    items = []
    i = 0
    for cat, n in _CAT_COUNTS.items():
        for _ in range(n):
            i += 1
            items.append({"id": f"q_{i:03d}", "category": cat})
    return items


def test_smoke_subset_size():
    items = _fake_items()
    subset = golden_set.smoke_subset(items, size=50)
    assert len(subset) == 50


def test_smoke_subset_covers_every_category():
    items = _fake_items()
    subset = golden_set.smoke_subset(items, size=50)
    assert {it["category"] for it in subset} == set(_CAT_COUNTS)


def test_smoke_subset_deterministic_across_runs():
    items = _fake_items()
    a = golden_set.smoke_subset(items, size=50)
    b = golden_set.smoke_subset(items, size=50)
    assert [x["id"] for x in a] == [x["id"] for x in b]


def test_select_full_loads_real_golden_set():
    items = golden_set.select("full")
    assert len(items) == 300


def test_select_smoke_stratified_on_real_golden_set():
    items = golden_set.select("smoke")
    assert len(items) == 50
    assert {it["category"] for it in items} == set(_CAT_COUNTS)


def test_select_targeted_requires_category():
    with pytest.raises(ValueError):
        golden_set.select("targeted")


def test_select_targeted_filters_by_category():
    items = golden_set.select("targeted", category="adversarial")
    assert items
    assert all(it["category"] == "adversarial" for it in items)


def test_select_unknown_mode_raises():
    with pytest.raises(ValueError):
        golden_set.select("bogus")
