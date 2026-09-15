import pytest
import json
from backend.services.intelligence_service import CaseIntelligenceEngine

def test_analyze_case_mocked(monkeypatch):
    class MockDocument:
        chunks = []

    class MockCase:
        id = 1
        analysis_status = "PENDING"
        case_name = "Old Name"
        case_number = "123"
        court = "High Court"
        legal_topics = ""
        executive_summary = ""
        court_reasoning = ""
        decision = ""
        documents = [MockDocument()]

    class MockDB:
        def query(self, *a, **k):
            class Q:
                def filter(self, *a, **k):
                    class F:
                        def first(self):
                            return MockCase()
                        def delete(self):
                            pass
                    return F()
            return Q()
        def commit(self): pass
        def add(self, *a): pass

    class MockResponse:
        text = json.dumps({
            "case_name": "New Name",
            "facts": [{"fact_type": "Material", "description": "fact 1"}]
        })

    class MockModel:
        def generate_content(self, *a, **k):
            return MockResponse()

    engine = CaseIntelligenceEngine()
    engine.model = MockModel()

    db = MockDB()
    case = engine.analyze_case(db, 1)

    assert case.analysis_status == "COMPLETED"
    assert case.case_name == "New Name"
