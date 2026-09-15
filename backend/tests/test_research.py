import pytest
from backend.models.domain import ResearchSession, ResearchCase, ResearchEvidence, ResearchNote

def test_research_session_models():
    # Simple struct test without hitting real DB to verify model config
    session = ResearchSession(
        id=1,
        title="Test Session",
        research_question="What is the test?"
    )
    
    assert session.title == "Test Session"
    assert session.research_question == "What is the test?"
    
    rc = ResearchCase(id=1, session_id=1, case_id=100)
    assert rc.case_id == 100
    
    re = ResearchEvidence(id=1, session_id=1, category="FACT", supporting_text="Text")
    assert re.category == "FACT"
    
    rn = ResearchNote(id=1, session_id=1, content="My note")
    assert rn.content == "My note"
