from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.domain import CompareRequest, ComparisonResponse
from backend.services.compare_service import compare_cases_service
from backend.routes.cases import get_case_detail
from backend.dependencies import get_current_user
from backend.models.domain import User

router = APIRouter()

@router.post("/", response_model=ComparisonResponse)
def compare_cases(request: CompareRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        # Get comparison analysis
        analysis = compare_cases_service(db, request.case_ids, request.research_question)
        
        # Load full case profiles for frontend to render in matrix
        cases = []
        for cid in request.case_ids:
            try:
                case_profile = get_case_detail(cid, db, current_user)
                cases.append(case_profile)
            except Exception:
                pass # skip missing
                
        analysis["cases"] = cases
        
        return analysis
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
