from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from backend.database import get_db
from backend.dependencies import get_optional_current_user
from backend.models.domain import User
from backend.schemas.domain import SearchRequest, SearchResultItem, ResearchRequest, ResearchResponse
from backend.services.search_service import search_service
from backend.services.rag_service import ask_legal_question

logger = logging.getLogger("lexora.api_routes")
router = APIRouter()

@router.post("/search", response_model=List[SearchResultItem])
def search_documents(
    request: SearchRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        results = search_service.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters,
            user=current_user,
            db=db
        )
        return results or []
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Search failed.")

@router.post("/rag/ask", response_model=ResearchResponse)
@router.post("/research/ask", response_model=ResearchResponse)
def research_documents(
    request: ResearchRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        import inspect
        kwargs = {"query": request.query, "top_k": request.top_k}
        sig = inspect.signature(ask_legal_question)
        if "context_filters" in sig.parameters:
            kwargs["context_filters"] = request.filters
        if "summary_mode" in sig.parameters:
            kwargs["summary_mode"] = request.summary_mode or "RESEARCH"
        if "user" in sig.parameters:
            kwargs["user"] = current_user
        if "db" in sig.parameters:
            kwargs["db"] = db
        import time
        start_t = time.time()
        results = ask_legal_question(**kwargs)
        elapsed_ms = (time.time() - start_t) * 1000.0

        # Privacy-safe pilot telemetry recording
        try:
            if current_user:
                from backend.services.monitoring_service import monitoring_service
                has_abstained = getattr(results, "has_abstained", False) or "abstain" in str(getattr(results, "answer", "")).lower()
                cits = getattr(results, "citations", []) or []
                monitoring_service.record_event(
                    user_id=current_user.id,
                    retrieval_mode="hybrid_rrf",
                    candidate_count=request.top_k,
                    latency_ms=elapsed_ms,
                    citations_validated=bool(cits),
                    citations_count=len(cits),
                    abstained=has_abstained,
                    status="SUCCESS",
                    query_text=request.query
                )
        except Exception as mon_err:
            logger.debug(f"Pilot monitoring non-critical log failure: {mon_err}")

        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Research failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Research failed.")
