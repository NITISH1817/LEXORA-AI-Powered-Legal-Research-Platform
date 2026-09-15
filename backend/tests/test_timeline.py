import pytest
from backend.services.intelligence_service import IntelligenceService
from backend.models.domain import CaseEvent, Case

class MockDB:
    def __init__(self):
        self.adds = []
        
    def add(self, item):
        self.adds.append(item)

def test_timeline_extraction_precision(monkeypatch):
    db = MockDB()
    mock_case = Case(id=1, case_name="Timeline Case")
    
    parsed = {
        "timeline": [
            {
                "event_date": None,
                "date_text": "around March 2022",
                "date_precision": "approximate",
                "event_type": "CONTRACT",
                "title": "Contract signed",
                "description": "Parties agreed...",
                "timeline_type": "FACTUAL",
                "page_number": 4,
                "supporting_text": "contract around March 2022"
            },
            {
                "event_date": "2024-05-15",
                "date_text": "15 May 2024",
                "date_precision": "exact",
                "event_type": "JUDGMENT",
                "title": "Final Order",
                "description": "Court ruled...",
                "timeline_type": "PROCEDURAL",
                "page_number": 12,
                "supporting_text": "passed on 15 May 2024"
            }
        ]
    }
    
    # Process simulated parsed data
    for ev in parsed.get("timeline", []):
        db.add(CaseEvent(
            case_id=mock_case.id,
            event_date=ev.get("event_date"),
            date_text=ev.get("date_text"),
            date_precision=ev.get("date_precision"),
            event_type=ev.get("event_type"),
            title=ev.get("title"),
            description=ev.get("description"),
            timeline_type=ev.get("timeline_type")
        ))
        
    assert len(db.adds) == 2
    
    # Verify the approximate date wasn't forcefully converted to exact YYYY-MM-DD
    approx_event = db.adds[0]
    assert approx_event.date_precision == "approximate"
    assert approx_event.event_date is None
    assert approx_event.date_text == "around March 2022"
    assert approx_event.timeline_type == "FACTUAL"
    
    # Verify exact date
    exact_event = db.adds[1]
    assert exact_event.date_precision == "exact"
    assert exact_event.event_date == "2024-05-15"
    assert exact_event.timeline_type == "PROCEDURAL"
