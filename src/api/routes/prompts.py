"""PromptOps endpoints — contract: docs/system/contracts/api_contracts.md.

POST /prompts                          — tạo prompt draft.
GET  /prompts/{prompt_id}/versions     — liệt kê versions.
GET  /prompts/{prompt_id}/diff         — unified diff giữa 2 version.
POST /prompts/{prompt_id}/activate     — activate; registry enforce
                                         eval_result_id-hoặc-override-logged.

POST /prompts/{id}/compare (contract) chạy OFFLINE qua
scripts/run_prompt_comparison.py thay vì endpoint — comparison tốn ~72
lượt gọi LLM/lần, không phù hợp request-response HTTP đồng bộ; sẽ thành
job async khi có eval engine (Phase 8). Ghi nhận ở CHECKLIST Phase 6.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.common.settings import get_settings
from src.promptops.diff import prompt_diff
from src.promptops.registry import PromptRegistry, PromptVersion, RegistryError
from src.promptops.renderer import RenderError

router = APIRouter(prefix="/prompts", tags=["prompts"])


def _registry() -> PromptRegistry:
    return PromptRegistry(get_settings().postgres_dsn)


class CreatePromptRequest(BaseModel):
    prompt_id: str = Field(min_length=3)
    prompt_version: str = Field(min_length=3)
    task_type: str = "qa"
    domain: str = "university_regulation_iuh"
    language: str = "vi"
    model_tier: str = "balanced"
    template: str = Field(min_length=10)
    variables: list[str] = ["context", "question"]
    created_by: str = "api"
    parent_version: str | None = None
    change_summary: str | None = None


class ActivateRequest(BaseModel):
    prompt_version: str
    actor: str
    override: bool = False
    override_reason: str | None = None


@router.post("", status_code=201)
async def create_prompt(req: CreatePromptRequest) -> dict:
    version = PromptVersion(**req.model_dump(), status="draft")
    try:
        _registry().create_version(version)
    except RenderError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error_code": "VALIDATION_ERROR", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001 - duplicate key / db down -> lỗi có mã rõ
        raise HTTPException(
            status_code=409,
            detail={"error_code": "CREATE_FAILED", "message": str(exc)[:200]},
        ) from exc
    return {"prompt_id": req.prompt_id, "prompt_version": req.prompt_version, "status": "draft"}


@router.get("/{prompt_id}/versions")
async def list_versions(prompt_id: str) -> dict:
    versions = _registry().list_versions(prompt_id)
    if not versions:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "PROMPT_NOT_FOUND", "message": f"prompt '{prompt_id}' không tồn tại"},
        )
    return {"prompt_id": prompt_id, "versions": versions}


@router.get("/{prompt_id}/diff")
async def diff_versions(prompt_id: str, from_version: str, to_version: str) -> dict:
    reg = _registry()
    try:
        old = reg.get(prompt_id, from_version)
        new = reg.get(prompt_id, to_version)
    except RegistryError as exc:
        raise HTTPException(
            status_code=404, detail={"error_code": "PROMPT_NOT_FOUND", "message": str(exc)}
        ) from exc
    return {
        "prompt_id": prompt_id,
        "from_version": from_version,
        "to_version": to_version,
        "diff": prompt_diff(old.template, new.template, from_version, to_version),
    }


@router.post("/{prompt_id}/activate")
async def activate(prompt_id: str, req: ActivateRequest) -> dict:
    try:
        _registry().activate(
            prompt_id, req.prompt_version,
            actor=req.actor, override=req.override, override_reason=req.override_reason,
        )
    except RegistryError as exc:
        raise HTTPException(
            status_code=409, detail={"error_code": "ACTIVATION_BLOCKED", "message": str(exc)}
        ) from exc
    return {"prompt_id": prompt_id, "active_version": req.prompt_version}
