import pytest
from evaluation.metrics import evaluate_faithfulness

def test_evaluate_faithfulness():
    required = ["case_001:page_5"]
    forbidden = ["plaintiff won"]
    
    # 1. Correct abstention
    score1 = evaluate_faithfulness("Insufficient evidence in the indexed authorities.", [], [])
    assert score1 == 1.0
    
    # 2. Correctly answered with citation
    score2 = evaluate_faithfulness("The contract was breached [case_001].", required, forbidden)
    assert score2 == 1.0
    
    # 3. Failed abstention (abstained when evidence was available)
    score3 = evaluate_faithfulness("Insufficient evidence in the indexed authorities.", required, [])
    assert score3 == 0.0
    
    # 4. Hallucination penalty
    score4 = evaluate_faithfulness("The plaintiff won the case.", required, forbidden)
    assert score4 == 0.0
