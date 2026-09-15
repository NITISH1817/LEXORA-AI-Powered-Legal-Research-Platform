from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models.domain import Case, CaseEvent, User
from backend.schemas.domain import CaseSchema, CaseDetailSchema, CaseEventSchema, TimelineResponse
from backend.services.intelligence_service import intelligence_engine
from backend.dependencies import get_current_user

router = APIRouter()

@router.get("/{case_id}", response_model=CaseDetailSchema)
def get_case_detail(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Build dictionary response explicitly because SQLAlchemy relationships might need manual grouping
    # For arguments:
    args_dict = {"Petitioner": [], "Respondent": []}
    for arg in case.party_arguments:
        if arg.party_type in args_dict:
            args_dict[arg.party_type].append(arg)
        else:
            args_dict[arg.party_type] = [arg]
            
    # Assemble CaseIntelligenceResponse structure mapped mostly automatically by from_attributes
    # but override arguments to match dictionary schema
    resp_dict = {
        "id": case.id,
        "case_name": case.case_name,
        "case_number": case.case_number,
        "court": case.court,
        "decision_date": case.decision_date,
        "executive_summary": case.executive_summary,
        "facts": case.facts,
        "issues": case.legal_issues,
        "arguments": args_dict,
        "court_reasoning": case.court_reasoning,
        "decision": case.decision,
        "principles": case.principles,
        "citations": [], # Phase 3 Citations (not fully modeled in response without citing_case)
        "timeline": case.timeline_events,
        "important_passages": case.important_passages,
        "analysis_status": case.analysis_status,
        "legal_topics": case.legal_topics
    }
    return resp_dict

@router.post("/{case_id}/analyze", response_model=None)
def analyze_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        case = intelligence_engine.analyze_case(db, case_id)
        return get_case_intelligence(case_id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{case_id}/timeline", response_model=None)
def get_case_timeline(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from backend.models.domain import CaseEvent
    
    events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).all()
    
    # Sort events. Use event_date if available (YYYY-MM-DD), else fallback (to avoid crash)
    # We put unknown dates at the top or bottom. We'll sort by event_date (nulls last)
    sorted_events = sorted(events, key=lambda x: x.event_date or "9999-12-31")
    
    factual = [e for e in sorted_events if e.timeline_type == "FACTUAL"]
    procedural = [e for e in sorted_events if e.timeline_type == "PROCEDURAL"]
    
    return {
        "case_id": case_id,
        "factual_events": factual,
        "procedural_events": procedural,
        "events": sorted_events
    }

@router.get("/{case_id}/citations")
def get_case_citations(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from backend.models.domain import CaseCitation
    
    outgoing = db.query(CaseCitation).filter(CaseCitation.source_case_id == case_id).all()
    incoming = db.query(CaseCitation).filter(CaseCitation.target_case_id == case_id).all()
    
    return {
        "case_id": case_id,
        "outgoing": outgoing,
        "incoming": incoming
    }

@router.get("/{case_id}/graph")
def get_case_graph(case_id: int, depth: int = 1, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Hardcap depth to 2 to protect sandbox resources
    max_depth = min(depth, 2)
    from backend.models.domain import CaseCitation, Case
    
    nodes = {}
    edges = []
    
    # Simple BFS to build graph
    queue = [(case_id, 0)]
    visited = set()
    
    while queue:
        curr_id, curr_depth = queue.pop(0)
        
        if curr_id in visited:
            continue
            
        visited.add(curr_id)
        
        # Add node
        curr_case = db.query(Case).filter(Case.id == curr_id).first()
        if curr_case and str(curr_id) not in nodes:
            nodes[str(curr_id)] = {
                "id": str(curr_id),
                "case_name": curr_case.case_name,
                "court": curr_case.court,
                "year": curr_case.year,
                "indexed": True
            }
            
        if curr_depth >= max_depth:
            continue
            
        # Get edges
        outgoing = db.query(CaseCitation).filter(CaseCitation.source_case_id == curr_id).all()
        for edge in outgoing:
            target_node_id = str(edge.target_case_id) if edge.target_case_id else f"unresolved_{edge.id}"
            
            # Add target node if unresolved
            if not edge.target_case_id and target_node_id not in nodes:
                nodes[target_node_id] = {
                    "id": target_node_id,
                    "case_name": edge.target_case_name or "Unknown Authority",
                    "court": None,
                    "year": None,
                    "indexed": False
                }
                
            edges.append({
                "id": str(edge.id),
                "source": str(curr_id),
                "target": target_node_id,
                "relationship": edge.relationship_type,
                "page": edge.page_number,
                "evidence": edge.supporting_text
            })
            
            if edge.target_case_id and edge.target_case_id not in visited:
                queue.append((edge.target_case_id, curr_depth + 1))
                
    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
