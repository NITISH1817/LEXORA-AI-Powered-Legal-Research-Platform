from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.database import get_db
from backend.models.domain import Case, CaseEvent, User, CaseCitation
from backend.schemas.domain import CaseDetailSchema, TimelineResponse, GraphResponse
from backend.services.intelligence_service import intelligence_engine
from backend.dependencies import get_current_user

logger = logging.getLogger("lexora.routes.cases")

router = APIRouter()

@router.get("/{case_id}", response_model=CaseDetailSchema)
def get_case_detail(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Authorization check
    if current_user.role != "ADMIN" and case.documents:
        for doc in case.documents:
            if doc.owner_id is not None and doc.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Case not found")

    # Group arguments by party type
    args_dict = {"Petitioner": [], "Respondent": []}
    for arg in case.party_arguments:
        if arg.party_type in args_dict:
            args_dict[arg.party_type].append(arg)
        else:
            args_dict[arg.party_type] = [arg]
            
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
        "citations": case.citations_made or [],
        "timeline": case.timeline_events,
        "important_passages": case.important_passages,
        "analysis_status": case.analysis_status,
        "legal_topics": case.legal_topics
    }
    return resp_dict

@router.post("/{case_id}/analyze", response_model=CaseDetailSchema)
def analyze_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Authorization check
    if current_user.role != "ADMIN" and case.documents:
        for doc in case.documents:
            if doc.owner_id is not None and doc.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Case not found")

    try:
        intelligence_engine.analyze_case(db, case_id)
        return get_case_detail(case_id, db, current_user)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail="Case not found")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Case analysis failed for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Case analysis failed.")

@router.get("/{case_id}/timeline", response_model=TimelineResponse)
def get_case_timeline(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Authorization check
    if current_user.role != "ADMIN" and case.documents:
        for doc in case.documents:
            if doc.owner_id is not None and doc.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Case not found")

    from backend.services.timeline_service import get_case_timeline_data
    return get_case_timeline_data(case_id, db)

@router.get("/{case_id}/citations")
def get_case_citations(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Authorization check
    if current_user.role != "ADMIN" and case.documents:
        for doc in case.documents:
            if doc.owner_id is not None and doc.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Case not found")

    outgoing = db.query(CaseCitation).filter(CaseCitation.source_case_id == case_id).all()
    incoming = db.query(CaseCitation).filter(CaseCitation.target_case_id == case_id).all()
    
    return {
        "case_id": case_id,
        "outgoing": outgoing,
        "incoming": incoming
    }

ALLOWED_RELATIONSHIPS = {"CITES", "FOLLOWS", "DISTINGUISHES", "OVERRULES", "REVERSES", "APPLIES", "REFERENCES"}
MAX_GRAPH_NODES = 50
MAX_GRAPH_EDGES = 100

@router.get("/{case_id}/graph", response_model=GraphResponse)
def get_case_graph(
    case_id: int,
    depth: int = Query(1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if depth < 1:
        raise HTTPException(status_code=400, detail="Depth must be at least 1")
    if depth > 4:
        raise HTTPException(status_code=400, detail="Depth cannot exceed 4")

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Authorization check on root case
    if current_user.role != "ADMIN" and case.documents:
        for doc in case.documents:
            if doc.owner_id is not None and doc.owner_id != current_user.id:
                raise HTTPException(status_code=404, detail="Case not found")

    max_depth = min(depth, 4)
    nodes = {}
    edges = []
    seen_edges = set()  # (source_id, target_id, relationship) for deduplication

    # Add root node
    nodes[str(case.id)] = {
        "id": str(case.id),
        "case_name": case.case_name,
        "court": case.court,
        "year": case.year,
        "indexed": True
    }

    # BFS traversal with cycle protection
    queue = [(case_id, 0)]
    visited = set()

    while queue and len(nodes) < MAX_GRAPH_NODES and len(edges) < MAX_GRAPH_EDGES:
        curr_id, curr_depth = queue.pop(0)

        if curr_id in visited:
            continue
        visited.add(curr_id)

        # Ensure node exists in node map
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

        # Get outgoing citations
        outgoing = db.query(CaseCitation).filter(CaseCitation.source_case_id == curr_id).all()
        for edge in outgoing:
            if len(edges) >= MAX_GRAPH_EDGES:
                break

            target_node_id = str(edge.target_case_id) if edge.target_case_id else f"unresolved_{edge.id}"

            # Check authorization if target is a real case in database
            if edge.target_case_id:
                target_case = db.query(Case).filter(Case.id == edge.target_case_id).first()
                if target_case:
                    if current_user.role != "ADMIN" and target_case.documents:
                        is_private = any(
                            d.owner_id is not None and d.owner_id != current_user.id
                            for d in target_case.documents
                        )
                        if is_private:
                            continue  # Do not include private target case

                    if str(edge.target_case_id) not in nodes and len(nodes) < MAX_GRAPH_NODES:
                        nodes[str(edge.target_case_id)] = {
                            "id": str(edge.target_case_id),
                            "case_name": target_case.case_name,
                            "court": target_case.court,
                            "year": target_case.year,
                            "indexed": True
                        }
            else:
                # Unresolved target node
                if target_node_id not in nodes and len(nodes) < MAX_GRAPH_NODES:
                    nodes[target_node_id] = {
                        "id": target_node_id,
                        "case_name": edge.target_case_name or "Unknown Authority",
                        "court": None,
                        "year": None,
                        "indexed": False
                    }

            # Relationship normalization
            raw_rel = (edge.relationship_type or "CITES").strip().upper()
            rel = raw_rel if raw_rel in ALLOWED_RELATIONSHIPS else "CITES"

            # Deduplication of repeated citations
            edge_sig = (str(curr_id), target_node_id, rel)
            if edge_sig in seen_edges:
                continue
            seen_edges.add(edge_sig)

            has_evidence = bool(edge.supporting_text and edge.supporting_text.strip())
            edges.append({
                "id": str(edge.id),
                "source": str(curr_id),
                "target": target_node_id,
                "relationship": rel,
                "page": edge.page_number,
                "evidence": edge.supporting_text or "",
                "verification_status": "VERIFIED" if has_evidence else "UNVERIFIED",
                "confidence": 1.0 if has_evidence else 0.8
            })

            # Queue target for next depth level if not yet visited
            if edge.target_case_id and edge.target_case_id not in visited and len(nodes) < MAX_GRAPH_NODES:
                queue.append((edge.target_case_id, curr_depth + 1))

    return {
        "nodes": list(nodes.values()),
        "edges": edges
    }
