import google.generativeai as genai
import json
import logging
from backend.config import settings
from sqlalchemy.orm import Session
from backend.models.domain import Case, LegalPrinciple

logger = logging.getLogger("lexora.services.precedent")

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash') if settings.GEMINI_API_KEY else None

def extract_case_intelligence(text: str) -> dict:
    """
    Analyzes raw case text and extracts structured intelligence fields.
    """
    if not settings.GEMINI_API_KEY or not model:
        return {}
        
    prompt = f"""
    You are an elite Legal Intelligence Analyst. Analyze the following court judgment text.
    Extract the core legal intelligence and return ONLY a valid JSON object with this exact schema:
    {{
        "executive_summary": "1-2 sentence high-level summary",
        "facts": "A concise summary of the material facts",
        "issues": "The primary legal questions before the court",
        "procedural_history": "How the case arrived at this court",
        "court_reasoning": "The core logic and ratio decidendi used by the court",
        "decision": "The final outcome/holding",
        "remedy": "Any damages, injunctions, or orders issued",
        "category": "The primary area of law (e.g., Contract Law, Constitutional Law)",
        "legal_principles": [
            {{
                "principle_name": "Short name for the doctrine",
                "description": "Explanation of how the rule was applied"
            }}
        ]
    }}
    
    Case Text:
    {text[:15000]}  # Limiting text to prevent context overload if the PDF is massive
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(response_text)
        return parsed
    except Exception as e:
        logger.error(f"Intelligence Extraction Error: {e}")
        return {}

def update_case_with_intelligence(db: Session, case: Case, intelligence: dict) -> Case:
    """
    Applies extracted intelligence to the Case model using verified scalar fields
    and persists related ORM objects safely.
    """
    # Scalar summaries — NEVER assign strings directly to ORM relationship collections
    case.executive_summary = intelligence.get("executive_summary") or case.executive_summary or ""
    case.facts_summary = intelligence.get("facts") or case.facts_summary or ""
    case.legal_issues_summary = intelligence.get("issues") or case.legal_issues_summary or ""
    case.procedural_history = intelligence.get("procedural_history") or case.procedural_history or ""
    case.court_reasoning = intelligence.get("court_reasoning") or case.court_reasoning or ""
    case.decision = intelligence.get("decision") or case.decision or ""
    case.remedy = intelligence.get("remedy") or case.remedy or ""
    if intelligence.get("category"):
        case.category = intelligence.get("category")
        
    # Clear existing principles for idempotency before populating verified ORM objects
    db.query(LegalPrinciple).filter(LegalPrinciple.case_id == case.id).delete()
    
    principles = intelligence.get("legal_principles", [])
    for p in principles:
        p_name = p.get("principle_name", "").strip()
        p_desc = p.get("description", "").strip()
        
        if p_name and p_desc:
            desc = f"{p_name}: {p_desc}"
        else:
            desc = p_desc or p_name
            
        if desc:
            new_principle = LegalPrinciple(
                case_id=case.id,
                description=desc
            )
            db.add(new_principle)
            
    return case

def process_case_intelligence(db: Session, case_id: int, full_text: str = "", intelligence: dict = None) -> bool:
    """
    Extracts intelligence and updates the Case database model.
    """
    if intelligence is None:
        intelligence = extract_case_intelligence(full_text)
        
    if not intelligence:
        return False
        
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return False
        
    update_case_with_intelligence(db, case, intelligence)
    db.commit()
    db.refresh(case)
    return True
