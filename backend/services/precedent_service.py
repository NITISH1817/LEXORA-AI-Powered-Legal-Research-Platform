import google.generativeai as genai
import json
from backend.config import settings
from sqlalchemy.orm import Session
from backend.models.domain import Case, LegalPrinciple

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

def extract_case_intelligence(text: str) -> dict:
    """
    Analyzes raw case text and extracts structured intelligence fields.
    """
    if not settings.GEMINI_API_KEY:
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
        print(f"Intelligence Extraction Error: {e}")
        return {}

def process_case_intelligence(db: Session, case_id: int, full_text: str):
    """
    Extracts intelligence and updates the Case database model.
    """
    intelligence = extract_case_intelligence(full_text)
    if not intelligence:
        return False
        
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return False
        
    # Update Case Model with Intelligence
    case.executive_summary = intelligence.get("executive_summary", "")
    case.facts = intelligence.get("facts", "")
    case.issues = intelligence.get("issues", "")
    case.procedural_history = intelligence.get("procedural_history", "")
    case.court_reasoning = intelligence.get("court_reasoning", "")
    case.decision = intelligence.get("decision", "")
    case.remedy = intelligence.get("remedy", "")
    case.category = intelligence.get("category", "")
    
    # Save Legal Principles
    principles = intelligence.get("legal_principles", [])
    for p in principles:
        new_principle = LegalPrinciple(
            case_id=case.id,
            principle_name=p.get("principle_name", ""),
            description=p.get("description", "")
        )
        db.add(new_principle)
        
    db.commit()
    return True
