"""Feedback Loop endpoints (Phase 11, Module 9) — contract: none formal
yet (module added after api_contracts.md was written for Phase 5); shape
follows the same request/response style as src/api/routes/prompts.py.

POST /feedback              — submit feedback linked to a trace_id; looks
                              the trace up via RagService.get_trace()
                              (in-memory 500-request window, same limit as
                              GET /qa/traces/{id}) to auto-classify an
                              error_label.
GET  /feedback/queue        — open feedback, human review queue.
GET  /feedback/clusters     — feedback grouped by (error_label, category).
POST /feedback/{id}/review  — mark reviewed by a human.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.api.routes.qa import get_service
from src.common.settings import get_settings
from src.feedback.classifier import classify_error_label
from src.feedback.clustering import cluster_feedback
from src.feedback.schemas import FeedbackType
from src.feedback.store import FeedbackStore, FeedbackStoreError
from src.rag.trace_store import new_id

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _store() -> FeedbackStore:
    return FeedbackStore(get_settings().postgres_dsn)


class SubmitFeedbackRequest(BaseModel):
    trace_id: str
    feedback_type: FeedbackType
    comment: str | None = None
    rating: int | None = None


class ReviewRequest(BaseModel):
    reviewer: str
    note: str | None = None
    status: str = "reviewed"


@router.post("", status_code=201)
async def submit_feedback(req: SubmitFeedbackRequest) -> dict:
    trace = get_service().get_trace(req.trace_id)
    if trace is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "TRACE_NOT_FOUND",
                "message": (
                    f"Không tìm thấy trace {req.trace_id} trong cửa sổ gần nhất "
                    "(500 request, giống GET /qa/traces/{id})."
                ),
            },
        )
    error_label = classify_error_label(trace, req.feedback_type)
    record = _store().create(
        feedback_id=new_id("fb"),
        trace_id=req.trace_id,
        feedback_type=req.feedback_type,
        error_label=error_label,
        comment=req.comment,
        rating=req.rating,
        source="user",
    )
    return {"feedback_id": record.feedback_id, "error_label": record.error_label}


@router.get("/queue")
async def review_queue() -> dict:
    open_items = _store().list_open()
    clusters = cluster_feedback(open_items)
    ordered_ids = [fid for c in clusters for fid in c.feedback_ids]
    by_id = {r.feedback_id: r for r in open_items}
    return {
        "total_open": len(open_items),
        "items": [
            {
                "feedback_id": fid,
                "trace_id": by_id[fid].trace_id,
                "feedback_type": by_id[fid].feedback_type,
                "error_label": by_id[fid].error_label,
                "category": by_id[fid].category,
                "comment": by_id[fid].comment,
                "created_at": by_id[fid].created_at,
            }
            for fid in ordered_ids
        ],
    }


@router.get("/clusters")
async def feedback_clusters() -> dict:
    all_items = _store().list_all()
    clusters = cluster_feedback(all_items)
    return {
        "total_feedback": len(all_items),
        "clusters": [
            {
                "error_label": c.error_label,
                "category": c.category,
                "size": c.size,
                "sample_questions": c.sample_questions,
            }
            for c in clusters
        ],
    }


@router.post("/{feedback_id}/review")
async def review_feedback(feedback_id: str, req: ReviewRequest) -> dict:
    try:
        _store().mark_reviewed(feedback_id, reviewer=req.reviewer, note=req.note, status=req.status)
    except FeedbackStoreError as exc:
        raise HTTPException(
            status_code=404, detail={"error_code": "FEEDBACK_NOT_FOUND", "message": str(exc)}
        ) from exc
    return {"feedback_id": feedback_id, "status": req.status}
