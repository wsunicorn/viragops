"""Prompt rendering with variable validation (Module 4).

`str.format`-based on purpose: templates carry literal JSON braces as
{{ }} and named placeholders like {context} — no new syntax to learn, no
template-engine dependency. `extract_variables` ignores escaped braces so
a template's declared `variables` list can be validated against what the
template actually uses (mismatch = registry data error, caught at write
time in the registry rather than at request time in the runtime).
"""

from __future__ import annotations

import re

# {var} nhưng không phải {{...}} (escaped literal)
_PLACEHOLDER_RE = re.compile(r"(?<!\{)\{([a-zA-Z_][a-zA-Z0-9_]*)\}(?!\})")


class RenderError(ValueError):
    pass


def extract_variables(template: str) -> set[str]:
    return set(_PLACEHOLDER_RE.findall(template))


def validate_template(template: str, declared_variables: list[str]) -> None:
    used = extract_variables(template)
    declared = set(declared_variables)
    if used != declared:
        missing = declared - used
        undeclared = used - declared
        parts = []
        if missing:
            parts.append(f"declared but unused: {sorted(missing)}")
        if undeclared:
            parts.append(f"used but undeclared: {sorted(undeclared)}")
        raise RenderError(f"template/variables mismatch — {'; '.join(parts)}")


def render(template: str, variables: dict[str, str]) -> str:
    try:
        return template.format(**variables)
    except KeyError as exc:
        raise RenderError(f"missing variable {exc} for template") from exc
    except (IndexError, ValueError) as exc:
        raise RenderError(f"malformed template: {exc}") from exc
