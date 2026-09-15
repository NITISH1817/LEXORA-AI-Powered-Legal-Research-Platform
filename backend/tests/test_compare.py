import pytest
from backend.services.compare_service import compare_cases_service
import json

def test_compare_cases_validation():
    class MockDB:
        def query(self, *a, **k):
            return self
        def filter(self, *a, **k):
            return self
        def first(self):
            return None # Simulate no cases found

    db = MockDB()

    # Test less than 2 cases
    with pytest.raises(ValueError, match="between 2 and 5"):
        compare_cases_service(db, [1])

    # Test more than 5 cases
    with pytest.raises(ValueError, match="between 2 and 5"):
        compare_cases_service(db, [1, 2, 3, 4, 5, 6])

    # Test case not found
    with pytest.raises(ValueError, match="One or more cases could not be found"):
        compare_cases_service(db, [1, 2])

def test_compare_cases_success(monkeypatch):
    class MockCase:
        def __init__(self, cid):
            self.id = cid
            self.case_name = f"Case {cid}"
            self.court = "Court"
            self.year = 2024
            self.documents = []
            self.facts = []
            self.legal_issues = []
            self.court_reasoning = ""
            self.decision = ""
            self.principles = []

    class MockDB:
        def __init__(self):
            self.cases = {1: MockCase(1), 2: MockCase(2)}
            self.last_query = None
            
        def query(self, *a, **k):
            return self
            
        def filter(self, expr):
            # Hacky way to extract id for mock
            self.last_query = int(str(expr.right.value))
            return self
            
        def first(self):
            return self.cases.get(self.last_query)
            
        def add(self, *a): pass
        def commit(self): pass

    class MockResponse:
        text = json.dumps({
            "executive_comparison": "Test",
            "similarities": [{"claim": "Test claim", "sources": ["case_1"]}],
            "differences": [],
            "distinguishing_factors": [],
            "reasoning_comparison": [],
            "principle_comparison": [],
            "outcome_comparison": [],
            "potential_tensions": []
        })

    class MockModel:
        def generate_content(self, *a, **k):
            return MockResponse()

    import backend.services.compare_service
    backend.services.compare_service.model = MockModel()

    db = MockDB()
    result = compare_cases_service(db, [1, 2])
    
    assert "similarities" in result
    assert result["similarities"][0]["claim"] == "Test claim"
    assert "case_1" in result["similarities"][0]["sources"]
