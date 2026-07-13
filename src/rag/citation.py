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

# Ollama local fallback (qwen2.5:7b, xem config/litellm_config.yaml) đo thật
# 2026-07-13: model không chép nguyên chunk_id dài
# ("chunk_doc_qd1482_quy_che_tin_chi_structure_aware_0060") mà tự rút gọn
# thành hậu tố số ("0060") — không phải lỗi context-window (đã test cả
# num_ctx=4096 và 8192, kết quả giống hệt, xem CHECKLIST Phase 8), là hạn
# chế thật của model 7B khi phải chép nguyên văn 1 chuỗi dài. Suffix match
# CHỈ chấp nhận khi hậu tố khớp DUY NHẤT 1 chunk trong tập đã retrieve cho
# đúng request này (không tra toàn bộ corpus) — tránh biến 1 model yếu
# thành nguồn trích dẫn sai mà tưởng đúng.
_MIN_SUFFIX_LEN = 3


def _resolve_chunk_id(raw_id: str, by_id: dict[str, dict]) -> str | None:
    if raw_id in by_id:
        return raw_id
    if len(raw_id) < _MIN_SUFFIX_LEN:
        return None
    candidates = [cid for cid in by_id if cid.endswith(raw_id)]
    return candidates[0] if len(candidates) == 1 else None


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
    seen_raw: set[str] = set()
    seen_resolved: set[str] = set()
    for item in data.get("citations") or []:
        raw_id = item.get("chunk_id") if isinstance(item, dict) else None
        if not raw_id or raw_id in seen_raw:
            continue
        seen_raw.add(raw_id)
        resolved_id = _resolve_chunk_id(raw_id, by_id)
        if resolved_id is None:
            invalid.append(raw_id)
            continue
        if resolved_id in seen_resolved:
            continue  # 2 raw_id khác nhau (vd bản đầy đủ + hậu tố rút gọn) cùng trỏ 1 chunk thật
        seen_resolved.add(resolved_id)
        chunk = by_id[resolved_id]
        citations.append(
            Citation(
                document_id=chunk["document_id"],
                chunk_id=resolved_id,
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
