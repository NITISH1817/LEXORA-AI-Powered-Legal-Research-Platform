from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from backend.database import get_db
from backend.schemas.domain import CompareRequest, ComparisonResponse
from backend.services.compare_service import compare_cases_service
from backend.routes.cases import get_case_detail
from backend.dependencies import get_current_user
from backend.models.domain import User, Case

logger = logging.getLogger("lexora.routes.compare")

router = APIRouter()

@router.post("", response_model=ComparisonResponse)
@router.post("/", response_model=ComparisonResponse)
def compare_cases(
    request: CompareRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate case IDs input bounds and duplicates
    if not request.case_ids or len(request.case_ids) < 2 or len(request.case_ids) > 5:
        raise HTTPException(status_code=400, detail="Comparison requires between 2 and 5 distinct cases.")

    if len(set(request.case_ids)) != len(request.case_ids):
        raise HTTPException(status_code=400, detail="Duplicate case IDs provided for comparison.")

    # Authorization and existence checks
    for cid in request.case_ids:
        case = db.query(Case).filter(Case.id == cid).first()
        if not case:
            raise HTTPException(status_code=400, detail=f"One or more cases could not be found: Case with ID {cid} could not be found.")

        # Check document ownership authorization
        if current_user.role != "ADMIN" and case.documents:
            for doc in case.documents:
                if doc.owner_id is not None and doc.owner_id != current_user.id:
                    raise HTTPException(status_code=404, detail=f"Case with ID {cid} not found.")

    try:
        # Get comparison analysis
        analysis = compare_cases_service(db, request.case_ids, request.research_question)

        # Load full case profiles for frontend to render in matrix
        cases = []
        for cid in request.case_ids:
            case_profile = get_case_detail(cid, db, current_user)
            cases.append(case_profile)

        analysis["cases"] = cases
        return analysis

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(status_code=500, detail="Comparison failed.")
