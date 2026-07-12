"""LLM-as-a-Judge for generation metrics (Phase 8, contracts/metric_definitions.md).

One judge call per non-refusal answer, scored against the REAL context
chunks the runtime actually retrieved for that request (not against
ground_truth directly) — the model is only bound to what it was actually
allowed to see, so that's what faithfulness/hallucination must be checked
against. ground_truth is passed too, only to help judge answer_relevance
(did this answer address what was asked; paraphrase must not be punished).

Rubric returns 0.0/0.5/1.0 buckets rather than a free continuous 0-1
float — free continuous LLM self-scoring is a well-known miscalibration
failure mode; a 3-point scale is coarser but far more repeatable, and
cheap for a human reviewer to spot-check against the same rubric text.

Results are cached by a hash of (question, answer, context) so re-running
a report (e.g. after fixing report formatting) never re-spends judge
quota on unchanged answers.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.rag.gateway_client import Gateway, GatewayError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_PATH = PROJECT_ROOT / "data" / "eval" / "judge_cache.json"

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

RUBRIC = """Bạn là giám khảo đánh giá câu trả lời của một hệ thống hỏi-đáp quy chế \
đào tạo IUH. Chỉ dựa trên NGỮ CẢNH được cung cấp bên dưới để chấm — không dùng \
kiến thức ngoài ngữ cảnh, kể cả khi bạn biết câu trả lời đúng thực tế.

Câu hỏi: {question}

Ngữ cảnh (các đoạn trích hệ thống đã lấy để trả lời):
{context}

Câu trả lời của hệ thống: {answer}

Đáp án tham khảo (có thể diễn đạt khác, không cần trùng từng chữ): {ground_truth}

Chấm 4 tiêu chí, mỗi tiêu chí chọn đúng MỘT trong các mức {{0.0, 0.5, 1.0}} (riêng \
hallucination là true/false):
- faithfulness: câu trả lời có bám sát ngữ cảnh không (1.0 = mọi chi tiết đều có \
căn cứ trong ngữ cảnh, 0.5 = phần lớn có căn cứ nhưng có chi tiết không rõ nguồn, \
0.0 = phần lớn không có căn cứ trong ngữ cảnh).
- answer_relevance: câu trả lời có giải quyết đúng câu hỏi không (1.0 = trả lời \
đúng trọng tâm, 0.5 = trả lời một phần hoặc lạc đề nhẹ, 0.0 = không trả lời câu hỏi).
- context_relevance: ngữ cảnh được cung cấp có thực sự liên quan để trả lời câu hỏi \
này không (1.0 = liên quan trực tiếp, 0.5 = liên quan một phần, 0.0 = không liên quan).
- hallucination: câu trả lời có chứa thông tin KHÔNG có trong ngữ cảnh không (true/false).

Trả về DUY NHẤT JSON theo đúng schema, không thêm chữ nào khác:
{{"faithfulness": 0.0, "answer_relevance": 0.0, "context_relevance": 0.0, \
"hallucination": false, "reasoning": "một câu ngắn giải thích"}}"""


@dataclass
class JudgeScore:
    faithfulness: float
    answer_relevance: float
    context_relevance: float
    hallucination: bool
    reasoning: str
    from_cache: bool = False


def _cache_key(question: str, answer: str, context: str) -> str:
    return hashlib.sha256(f"{question}|{answer}|{context}".encode()).hexdigest()[:24]


def _parse_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\s*|\s*```$", "", text, flags=re.IGNORECASE)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_RE.search(text)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


class JudgeCache:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or DEFAULT_CACHE_PATH
        self._data: dict[str, dict] = {}
        if self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def get(self, key: str) -> dict | None:
        return self._data.get(key)

    def set(self, key: str, value: dict) -> None:
        self._data[key] = value
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=1), encoding="utf-8"
        )


class GeminiJudge:
    def __init__(self, gateway: Gateway, cache: JudgeCache | None = None, tier: str = "judge") -> None:
        self._gateway = gateway
        self._cache = cache if cache is not None else JudgeCache()
        self._tier = tier

    def score(self, question: str, answer: str, context: str, ground_truth: str) -> JudgeScore:
        key = _cache_key(question, answer, context)
        cached = self._cache.get(key)
        if cached is not None:
            return JudgeScore(**cached, from_cache=True)

        prompt = RUBRIC.format(
            question=question, context=context[:6000], answer=answer,
            ground_truth=ground_truth or "(không có)",
        )
        gen = self._gateway.generate(tier=self._tier, prompt=prompt, json_output=True)
        data = _parse_json(gen.text)
        if data is None:
            # Judge output không parse được -> KHÔNG bịa điểm; ném lỗi để tầng
            # gọi loại câu này khỏi trung bình thay vì âm thầm tính sai lệch.
            raise GatewayError(f"judge output not parseable: {gen.text[:200]!r}")

        try:
            result = {
                "faithfulness": float(data["faithfulness"]),
                "answer_relevance": float(data["answer_relevance"]),
                "context_relevance": float(data["context_relevance"]),
                "hallucination": bool(data["hallucination"]),
                "reasoning": str(data.get("reasoning", "")),
            }
        except (KeyError, TypeError, ValueError) as exc:
            raise GatewayError(f"judge output missing/invalid fields: {data!r}") from exc

        self._cache.set(key, result)
        return JudgeScore(**result, from_cache=False)
