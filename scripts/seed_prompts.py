"""Seed the prompt registry with the 6 initial variants P0-P5 (Phase 6).

Idempotent: existing versions are left untouched (create_version
if_absent=True) — reruns never overwrite templates that may have been
evaluated/activated since. New versions land as status='testing' (they
are the planned experiment set, not ad-hoc drafts).

Bootstrap activation: p1_grounded_v1 is activated with an EXPLICIT LOGGED
OVERRIDE if (and only if) the prompt has no active version yet — the
runtime needs one active prompt to serve, and p1 is the template already
verified end-to-end in Phase 5. The comparison flow
(scripts/run_prompt_comparison.py) supersedes this with a data-driven
activation.

Usage:
    python scripts/seed_prompts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.common.settings import get_settings  # noqa: E402
from src.promptops.registry import PromptRegistry, PromptVersion, RegistryError  # noqa: E402
from src.promptops.templates import COMMON_METADATA, SEED_PROMPTS  # noqa: E402


def main() -> int:
    registry = PromptRegistry(get_settings().postgres_dsn)

    created = 0
    for seed in SEED_PROMPTS:
        version = PromptVersion(
            **COMMON_METADATA,
            prompt_version=seed["prompt_version"],
            template=seed["template"],
            change_summary=seed["change_summary"],
            status="testing",
        )
        if registry.create_version(version, if_absent=True):
            created += 1
            print(f"created {seed['prompt_version']}")
        else:
            print(f"exists  {seed['prompt_version']} (untouched)")

    prompt_id = COMMON_METADATA["prompt_id"]
    try:
        active = registry.get_active(prompt_id)
        print(f"active version: {active.prompt_version}")
    except RegistryError:
        registry.activate(
            prompt_id, "p1_grounded_v1",
            actor="seed_script_phase6",
            override=True,
            override_reason=(
                "bootstrap: chua co eval run chinh thuc; p1 da verify end-to-end o Phase 5 "
                "(xem modules/03). Se duoc thay bang activation theo so lieu tu "
                "run_prompt_comparison.py"
            ),
        )
        print("bootstrap-activated p1_grounded_v1 (override, logged)")

    print(f"done: {created} new version(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
