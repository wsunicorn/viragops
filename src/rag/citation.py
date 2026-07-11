"""Parse and validate the model's JSON output (Phase 5).

Guardrail (modules/03_rag_runtime_model_gateway.md): "Citation phải tham
chiếu chunk/source có thật" — any citation whose chunk_id is not among
the chunks actually retrieved for THIS request is dropped (and counted,
for the trace) rather than passed through: a fabricated citation is worse
than a missing one. If the model answered without any valid citation and
the policy requires one (config/prompts.yaml `require_citation: true`),
the answer is downgraded to a refusal — an unsourced answer must never
reach the user as if it were grounded.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from src.rag.schemas import Citation

_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class ParsedAnswer:
    answer: str
    citations: list[Citation]
    refusal: bool
    parse_error: str | None = None
    invalid_citations: list[str] = field(default_factory=list)  # chunk_id bịa/không thuộc retrieved


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_BLOCK_RE.search(text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def parse_model_output(
    raw_text: str,
    retrieved_chunks: list[dict[str, Any]],
    require_citation: bool = True,
) -> ParsedAnswer:
    data = _extract_json(raw_text)
    if data is None or not isinstance(data, dict):
        # Output không parse được -> từ chối an toàn thay vì trả text thô
        # không kiểm chứng được citation.
        return ParsedAnswer(
            answer="Hệ thống không xử lý được câu trả lời từ mô hình. Vui lòng thử lại.",
            citations=[],
            refusal=True,
            parse_error="unparseable_model_output",
        )

    refusal = bool(data.get("refusal", False))
    answer = str(data.get("answer", "")).strip()

    by_id = {c["chunk_id"]: c for c in retrieved_chunks}
    citations: list[Citation] = []
    invalid: list[str] = []
    seen: set[str] = set()
    for item in data.get("citations") or []:
        chunk_id = item.get("chunk_id") if isinstance(item, dict) else None
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        chunk = by_id.get(chunk_id)
        if chunk is None:
            invalid.append(chunk_id)
            continue
        citations.append(
            Citation(
                document_id=chunk["document_id"],
                chunk_id=chunk_id,
                section=chunk.get("section"),
                page=chunk.get("page_start"),
                quote=chunk["text"][:200],
            )
        )

    if not refusal and require_citation and not citations:
        return ParsedAnswer(
            answer=(
                "Tài liệu hiện có không đủ căn cứ được kiểm chứng để trả lời câu hỏi này."
            ),
            citations=[],
            refusal=True,
            parse_error="answer_without_valid_citation",
            invalid_citations=invalid,
        )

    if refusal and not answer:
        answer = "Tài liệu hiện có không chứa thông tin để trả lời câu hỏi này."

    return ParsedAnswer(
        answer=answer, citations=citations, refusal=refusal, invalid_citations=invalid
    )
