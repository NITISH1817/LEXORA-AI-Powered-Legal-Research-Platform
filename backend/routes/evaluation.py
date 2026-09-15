from fastapi import APIRouter, Depends, HTTPException
import os
import json
from backend.dependencies import require_role
from backend.models.domain import User

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

@router.get("/latest")
def get_latest_evaluation(current_user: User = Depends(require_role(["ADMIN"]))):
    try:
        results_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "evaluation", "results", "latest.json")
        if os.path.exists(results_file):
            with open(results_file, 'r') as f:
                return json.load(f)
        return {"status": "No evaluation results found"}
    except Exception as e:
        return {"error": str(e)}
