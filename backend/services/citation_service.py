import re
import google.generativeai as genai
from backend.config import settings
from sqlalchemy.orm import Session
from backend.models.domain import Citation, Case

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

def extract_citations_from_text(text: str) -> list[dict]:
    """
    Uses Regex to find potential legal citations in text.
    For an Indian legal context, we look for formats like:
    - [Year] X SCC Y
    - AIR [Year] SC/HC Y
    - Party A v. Party B
    """
    citations = []
    
    # Simple regex for "v." or "vs." case formats
    case_name_pattern = r'([A-Z][a-zA-Z\s\&\.\,]+)\s+v\.\s+([A-Z][a-zA-Z\s\&\.\,]+)'
    
    matches = re.finditer(case_name_pattern, text)
    for match in matches:
        full_match = match.group(0).strip()
        
        # Get context (50 chars before and after)
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context = text[start:end].replace('\n', ' ').strip()
        
        citations.append({
            "cited_case_name": full_match,
            "context": context
        })
        
    return citations

def analyze_citation_relationship(context: str) -> str:
    """Uses LLM to determine the relationship type of the citation."""
    if not settings.GEMINI_API_KEY:
        return "REFERENCES"
        
    prompt = f"""
    Analyze this legal text passage and determine how the cited authority is being treated.
    Return ONLY ONE of the following tags:
    - FOLLOWS (if the court agrees with or relies on the citation)
    - DISTINGUISHES (if the court says the citation does not apply to the current facts)
    - OVERRULES (if a higher court strikes down the cited decision)
    - REFERENCES (if it is just mentioned generally or historically)
    
    Passage: "{context}"
    """
    try:
        response = model.generate_content(prompt)
        tag = response.text.strip().upper()
        if tag in ["FOLLOWS", "DISTINGUISHES", "OVERRULES", "REFERENCES"]:
            return tag
        return "REFERENCES"
    except Exception:
        return "REFERENCES"

def process_and_save_citations(db: Session, citing_case_id: int, text: str):
    """Extracts, analyzes, and saves citations to the database."""
    extracted = extract_citations_from_text(text)
    
    saved_count = 0
    for cit in extracted:
        case_name = cit["cited_case_name"]
        
        # Check if we already have this exact citation for this case to avoid duplicates
        existing = db.query(Citation).filter(
            Citation.citing_case_id == citing_case_id,
            Citation.cited_case_name == case_name
        ).first()
        
        if existing:
            continue
            
        # Optional: Try to link to an existing case in our DB by name
        cited_case = db.query(Case).filter(Case.case_name.ilike(f"%{case_name}%")).first()
        cited_case_id = cited_case.id if cited_case else None
        
        relationship = analyze_citation_relationship(cit["context"])
        
        db_citation = Citation(
            citing_case_id=citing_case_id,
            cited_case_id=cited_case_id,
            cited_case_name=case_name,
            context=cit["context"],
            relationship_type=relationship
        )
        db.add(db_citation)
        saved_count += 1
        
    db.commit()
    return saved_count
