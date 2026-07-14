"""Seed the prompt registry with the initial prompt variants (Phase 6).

Idempotent: existing versions are left untouched (create_version
if_absent=True) — reruns never overwrite templates that may have been
evaluated/activated since. New versions land as status='testing' (they
are the planned experiment set, not ad-hoc drafts).

Bootstrap activation: PRODUCTION_PROMPT_VERSION is activated with an
EXPLICIT LOGGED OVERRIDE if (and only if) the prompt has no active
version yet — the runtime needs one active prompt to serve. This constant
tracks the REAL, already-validated activation decision chain
(p1 -> p6 -> p7, see docs/system/CHECKLIST_IMPLEMENTATION.md Phase 8
"Sửa citation accuracy multi-hop/ambiguous" for the live comparison data
behind each step) — it exists because that decision only ever got applied
to whichever Postgres was running locally at the time via
PromptRegistry.activate(); a fresh database (a new dev machine, or CI's
snapshot-restored Postgres — see .github/workflows/ci.yml
quality-gate-live) has no memory of it and would otherwise silently
bootstrap back to the outdated p1 default. Bumping this constant is the
one line that needs to change here when a future comparison run
supersedes p7 for real.

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

PRODUCTION_PROMPT_VERSION = "p7_citation_complete_safe_v1"


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
            prompt_id, PRODUCTION_PROMPT_VERSION,
            actor="seed_script_phase6",
            override=True,
            override_reason=(
                f"bootstrap: database moi khong co lich su activate — {PRODUCTION_PROMPT_VERSION} "
                "la ket qua that cua chuoi so sanh du lieu that p1->p6->p7 (xem "
                "docs/system/CHECKLIST_IMPLEMENTATION.md Phase 8 'Sua citation accuracy "
                "multi-hop/ambiguous'), replay lai quyet dinh do cho database nay thay vi "
                "quay ve p1 mac dinh cu"
            ),
        )
        print(f"bootstrap-activated {PRODUCTION_PROMPT_VERSION} (override, logged)")

    print(f"done: {created} new version(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
