"""Context assembly + prompt provider for the QA runtime.

Phase 6: the template no longer lives in code — the runtime resolves the
ACTIVE version from the prompt registry (PostgreSQL, Module 4) at startup
and renders it via src/promptops/renderer.py. This module keeps:

- `format_context()` — turning retrieved chunks into the {context}
  variable (chunk_id headers so the model can cite);
- `PromptProvider` protocol + implementations: `RegistryPromptProvider`
  (production) and `StaticPromptProvider` (tests/offline — mirrors the
  gateway Mock pattern so integration tests don't need Postgres).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from src.promptops.renderer import render


@dataclass
class ActivePrompt:
    version: str
    template: str


class PromptProvider(Protocol):
    def get_active(self) -> ActivePrompt: ...


class RegistryPromptProvider:
    """Resolves the active version from the PostgreSQL registry once and
    caches it — a server restart picks up newly-activated prompts, which
    matches the Phase 6 activation flow (activate -> redeploy/restart)."""

    def __init__(self, dsn: str, prompt_id: str = "rag_qa_vi") -> None:
        from src.promptops.registry import PromptRegistry

        self._registry = PromptRegistry(dsn)
        self._prompt_id = prompt_id
        self._cached: ActivePrompt | None = None

    def get_active(self) -> ActivePrompt:
        if self._cached is None:
            version = self._registry.get_active(self._prompt_id)
            self._cached = ActivePrompt(
                version=version.prompt_version, template=version.template
            )
        return self._cached


class StaticPromptProvider:
    def __init__(self, template: str, version: str = "static_test_v0") -> None:
        self._prompt = ActivePrompt(version=version, template=template)

    def get_active(self) -> ActivePrompt:
        return self._prompt


def format_context(chunks: list[dict[str, Any]], max_chars_per_chunk: int = 2500) -> str:
    blocks = []
    for c in chunks:
        header = f"[{c['chunk_id']}]"
        if c.get("section"):
            header += f" ({c['metadata'].get('document_title', c['document_id'])} — {c['section']})"
        else:
            header += f" ({c['metadata'].get('document_title', c['document_id'])})"
        blocks.append(f"{header}\n{c['text'][:max_chars_per_chunk]}")
    return "\n\n---\n\n".join(blocks)


def build_qa_prompt(question: str, chunks: list[dict[str, Any]], template: str) -> str:
    return render(template, {"context": format_context(chunks), "question": question})
