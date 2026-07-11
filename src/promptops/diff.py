"""Unified diff between two prompt versions (Module 4)."""

from __future__ import annotations

import difflib


def prompt_diff(
    old_template: str, new_template: str, old_label: str, new_label: str
) -> str:
    lines = difflib.unified_diff(
        old_template.splitlines(keepends=False),
        new_template.splitlines(keepends=False),
        fromfile=old_label,
        tofile=new_label,
        lineterm="",
    )
    return "\n".join(lines)
