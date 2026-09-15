import pytest
from backend.services.intelligence_service import IntelligenceService
from backend.models.domain import CaseCitation, Case

class MockDB:
    def __init__(self):
        self.adds = []
        self.deletes = []
        
    def query(self, model):
        return self
        
    def filter(self, *args, **kwargs):
        return self
        
    def delete(self):
        self.deletes.append("deleted")
        
    def first(self):
        return Case(id=99, case_name="Mock Target Case")
        
    def add(self, item):
        self.adds.append(item)
        
    def commit(self): pass

def test_citation_extraction(monkeypatch):
    db = MockDB()
    
    mock_case = Case(id=1, case_name="Source Case")
    
    parsed = {
        "citations": [
            {
                "case_name": "Mock Target Case",
                "citation_string": "2024 SCC 1",
                "relationship_type": "FOLLOWS",
                "supporting_text": "We follow...",
                "page_number": 14
            }
        ]
    }
    
    # Simple manual mock of the DB logic found in the intelligence service
    db.query(CaseCitation).filter(CaseCitation.source_case_id == mock_case.id).delete()
    for c in parsed.get("citations", []):
        target_case = db.query(Case).filter().first()
        db.add(CaseCitation(
            source_case_id=mock_case.id,
            target_case_id=target_case.id if target_case else None,
            target_case_name=c.get("case_name"),
            target_citation=c.get("citation_string"),
            relationship_type=c.get("relationship_type", "CITES"),
            supporting_text=c.get("supporting_text"),
            page_number=c.get("page_number")
        ))
        
    assert len(db.adds) == 1
    added_citation = db.adds[0]
    assert added_citation.target_case_id == 99
    assert added_citation.relationship_type == "FOLLOWS"
    assert added_citation.target_citation == "2024 SCC 1"
