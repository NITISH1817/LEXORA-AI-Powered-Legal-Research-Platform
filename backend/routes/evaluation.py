from fastapi import APIRouter, Depends, HTTPException, Body
import os
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.dependencies import get_current_user, require_role
from backend.models.domain import User
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])


class PilotFeedbackRequest(BaseModel):
    request_id: str = Field(..., description="The unique request identifier being evaluated")
    rating: Optional[int] = Field(None, ge=1, le=5, description="Quality rating from 1 to 5")
    review_status: str = Field("PENDING", description="Review status: PENDING, APPROVED, FLAGGED, REJECTED")
    review_notes: Optional[str] = Field(None, description="Optional qualitative notes from reviewer")
    flag_reason: Optional[str] = Field(None, description="Reason if flagged as incorrect or unsupported")


@router.get("/latest")
def get_latest_evaluation(current_user: User = Depends(require_role(["ADMIN"]))):
    """Returns the complete latest evaluation results JSON (Admin only)."""
    try:
        results_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "results", "latest.json")
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"status": "No evaluation results found"}
    except Exception as e:
        import logging
        logging.getLogger("lexora.routes.evaluation").error(f"Failed to load evaluation results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load evaluation results.")


@router.get("/reconciled")
def get_reconciled_metrics(current_user: User = Depends(require_role(["ADMIN", "RESEARCHER"]))):
    """
    Returns reconciled benchmark metrics distinguishing substantive answerable queries (N=55)
    from global aggregates (N=61), with cluster-aware bootstrap confidence intervals.
    """
    try:
        results_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "results", "latest.json")
        if os.path.exists(results_file):
            with open(results_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "benchmark_name": data.get("benchmark_metadata", {}).get("name"),
                    "version": data.get("benchmark_metadata", {}).get("version"),
                    "timestamp": data.get("timestamp"),
                    "reconciled_metrics": data.get("reconciled_metrics", {}),
                    "release_gate_status": data.get("release_gate_status", {})
                }
        return {"status": "No evaluation results found"}
    except Exception as e:
        import logging
        logging.getLogger("lexora.routes.evaluation").error(f"Failed to load reconciled metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load reconciled metrics.")


@router.post("/monitoring/feedback")
def submit_pilot_feedback(
    payload: PilotFeedbackRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Submits user feedback or attorney adjudication for a pilot research session.
    """
    record = monitoring_service.record_feedback(
        request_id=payload.request_id,
        user_id=current_user.id,
        rating=payload.rating,
        review_status=payload.review_status,
        review_notes=payload.review_notes,
        flag_reason=payload.flag_reason
    )
    if record is None:
        return {"status": "MONITORING_DISABLED", "message": "Pilot telemetry is currently disabled."}
    return {"status": "RECORDED", "feedback": record}


@router.get("/monitoring/summary")
def get_pilot_monitoring_summary(current_user: User = Depends(require_role(["ADMIN"]))):
    """
    Returns aggregated pilot telemetry statistics (Admin only).
    Enforces privacy by aggregating data and omitting individual query contents.
    """
    return monitoring_service.get_admin_summary()


@router.get("/monitoring/my-events")
def get_my_pilot_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """
    Returns the caller's own telemetry audit records (strict user isolation).
    """
    events = monitoring_service.get_user_events(user_id=current_user.id, limit=limit)
    return {"user_id": current_user.id, "count": len(events), "events": events}


@router.delete("/monitoring/my-events")
def delete_my_pilot_events(current_user: User = Depends(get_current_user)):
    """
    Deletes the caller's own audit and feedback records (privacy / right to be forgotten).
    """
    deleted = monitoring_service.delete_user_records(user_id=current_user.id)
    return {"status": "DELETED", "user_id": current_user.id, "deleted_records": deleted}
