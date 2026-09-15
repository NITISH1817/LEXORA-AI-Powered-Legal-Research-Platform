from fastapi import APIRouter, HTTPException
from typing import List
from backend.schemas.domain import SearchRequest, SearchResultItem
from backend.services.search_service import search_service
import logging

router = APIRouter()

@router.post("/search", response_model=List[SearchResultItem])
def search_documents(request: SearchRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        results = search_service.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        if not results:
            return []
            
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

from backend.schemas.domain import ResearchRequest, ResearchResponse
from backend.services.rag_service import ask_legal_question

@router.post("/research", response_model=ResearchResponse)
def research_documents(request: ResearchRequest):
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        results = ask_legal_question(
            query=request.query,
            top_k=request.top_k,
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Research failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")
