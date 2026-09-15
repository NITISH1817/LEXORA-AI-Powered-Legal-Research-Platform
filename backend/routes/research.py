from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
import json

from backend.database import get_db
from backend.models.domain import (
    ResearchSession, ResearchCase, ResearchEvidence, ResearchNote, Case, User
)
from backend.schemas.domain import (
    ResearchSessionSchema, ResearchSessionCreate, ResearchCaseCreate,
    ResearchEvidenceCreate, ResearchNoteCreate, ResearchNoteSchema
)
from backend.dependencies import get_current_user

router = APIRouter(prefix="/api/research", tags=["Research Session"])

@router.post("", response_model=ResearchSessionSchema)
def create_session(data: ResearchSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = ResearchSession(
        title=data.title,
        research_question=data.research_question,
        user_id=current_user.id
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("", response_model=List[ResearchSessionSchema])
def get_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Only return the user's sessions unless admin
    query = db.query(ResearchSession)
    if current_user.role != "ADMIN":
        query = query.filter(ResearchSession.user_id == current_user.id)
    return query.order_by(ResearchSession.updated_at.desc()).all()

@router.get("/{session_id}", response_model=ResearchSessionSchema)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"status": "deleted"}

@router.post("/{session_id}/cases")
def add_case(session_id: int, data: ResearchCaseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
    
    # check if already added
    existing = db.query(ResearchCase).filter(
        ResearchCase.session_id == session_id,
        ResearchCase.case_id == data.case_id
    ).first()
    
    if not existing:
        rc = ResearchCase(session_id=session_id, case_id=data.case_id)
        db.add(rc)
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
    return {"status": "success"}

@router.post("/{session_id}/evidence")
def add_evidence(session_id: int, data: ResearchEvidenceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
    
    re = ResearchEvidence(
        session_id=session_id,
        case_id=data.case_id,
        source_chunk_id=data.source_chunk_id,
        category=data.category,
        supporting_text=data.supporting_text,
        page_number=data.page_number
    )
    db.add(re)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success"}

@router.post("/{session_id}/notes", response_model=ResearchNoteSchema)
def add_note(session_id: int, data: ResearchNoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
    
    rn = ResearchNote(
        session_id=session_id,
        content=data.content,
        reference_case_id=data.reference_case_id
    )
    db.add(rn)
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rn)
    return rn

@router.post("/{session_id}/brief")
def generate_brief(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ResearchSession).filter(ResearchSession.id == session_id).first()
    if not session or (session.user_id != current_user.id and current_user.role != "ADMIN"):
        raise HTTPException(status_code=404, detail="Session not found")
        
    from backend.services.rag_service import generate_research_brief
    
    # Extract all evidence text
    evidence_items = []
    for ev in session.evidence:
        case_name = ev.case.case_name if ev.case else "Unknown Case"
        evidence_items.append({
            "case_name": case_name,
            "category": ev.category,
            "text": ev.supporting_text,
            "page": ev.page_number
        })
        
    cases = [{"name": rc.case.case_name, "court": rc.case.court, "year": rc.case.year} for rc in session.cases]
    
    try:
        brief = generate_research_brief(session.research_question, cases, evidence_items)
        return {"brief": brief}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
