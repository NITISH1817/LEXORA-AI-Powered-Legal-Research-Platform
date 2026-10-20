import re
import google.generativeai as genai
from backend.config import settings
from sqlalchemy.orm import Session
from backend.models.domain import Citation, Case

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash') if settings.GEMINI_API_KEY else None

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


def normalize_source_tag(tag: str, valid_source_keys: set[str]) -> str | None:
    """
    Normalizes a citation tag (e.g. '[S1]', 'S1', 's1', 'source_1', 'source 1')
    to its canonical valid source key (e.g. 'S1'). Returns None if no valid match.
    """
    if not tag:
        return None
    cleaned = tag.strip().strip("[]").strip()
    
    # Direct match
    if cleaned in valid_source_keys:
        return cleaned

    # Case-insensitive match
    for k in valid_source_keys:
        if cleaned.upper() == k.upper():
            return k

    # Format 'source_1' or 'source 1' -> 'S1'
    m = re.match(r'(?:source[\s_-]*)(\d+)', cleaned, re.IGNORECASE)
    if m:
        candidate = f"S{m.group(1)}"
        if candidate in valid_source_keys:
            return candidate

    # Format pure number '1' -> 'S1'
    if cleaned.isdigit():
        candidate = f"S{cleaned}"
        if candidate in valid_source_keys:
            return candidate

    return None


def validate_and_ground_citations(parsed: dict, source_map: dict[str, dict]) -> dict:
    """
    Evidence Verification and Citation Grounding Layer.
    
    Enforces that:
    1. Every cited source ID resolves to a genuine retrieved chunk in `source_map`.
    2. Model-produced metadata (case name, court, year, page) is replaced by true source metadata.
    3. Factual claims without evidence are flagged as [UNSUPPORTED].
    4. Hallucinated sources (e.g., [S99]) are removed.
    5. When evidence is insufficient, clear abstention is returned.
    """
    valid_keys = set(source_map.keys())

    # 1. Validate key findings
    verified_findings = []
    has_at_least_one_supported_finding = False
    for finding in parsed.get("key_findings", []):
        sources = finding.get("sources", [])
        valid_sources = []
        for s in sources:
            norm = normalize_source_tag(str(s), valid_keys)
            if norm and norm not in valid_sources:
                valid_sources.append(norm)

        text = finding.get("finding", "").strip()
        if valid_sources:
            has_at_least_one_supported_finding = True
            verified_findings.append({
                "finding": text,
                "sources": valid_sources
            })
        else:
            verified_findings.append({
                "finding": f"[UNSUPPORTED] {text} (Evidence insufficient in the indexed documents.)",
                "sources": []
            })

    # 2. Validate legal principles
    verified_principles = []
    for principle in parsed.get("legal_principles", []):
        sources = principle.get("sources", [])
        valid_sources = []
        for s in sources:
            norm = normalize_source_tag(str(s), valid_keys)
            if norm and norm not in valid_sources:
                valid_sources.append(norm)

        text = principle.get("principle", "").strip()
        if valid_sources:
            has_at_least_one_supported_finding = True
            verified_principles.append({
                "principle": text,
                "sources": valid_sources
            })
        else:
            verified_principles.append({
                "principle": f"[UNSUPPORTED] {text} (Evidence insufficient in the indexed documents.)",
                "sources": []
            })

    # 3. Validate authorities and overwrite metadata with source ground truth
    verified_authorities = []
    for auth in parsed.get("authorities", []):
        raw_sid = str(auth.get("source_id", ""))
        norm_sid = normalize_source_tag(raw_sid, valid_keys)
        if norm_sid and norm_sid in source_map:
            src = source_map[norm_sid]
            verified_authorities.append({
                "case_name": src.get("case_name", "Unknown Case"),
                "court": src.get("court", "Unknown Court"),
                "year": int(src.get("year", 0)),
                "page": int(src.get("page_number", 1)),
                "source_id": norm_sid
            })

    # 4. Validate inline citations in the answer text
    raw_answer = parsed.get("answer", "").strip()
    
    # Replace invalid inline citations like [S99] or [source_99]
    def replace_citation(match):
        inner = match.group(1)
        norm = normalize_source_tag(inner, valid_keys)
        if norm:
            return f"[{norm}]"
        return "[UNSUPPORTED CITATION]"

    grounded_answer = re.sub(r'\[([a-zA-Z0-9_\s-]+)\]', replace_citation, raw_answer)

    # 5. Abstention Enforcement: If no supported findings or answer already abstains
    abstain_phrases = ["insufficient evidence", "no sufficiently relevant authority", "no relevant evidence"]
    should_abstain = (
        not valid_keys or
        (not has_at_least_one_supported_finding and not verified_authorities) or
        any(phrase in raw_answer.lower() for phrase in abstain_phrases)
    )

    if should_abstain:
        grounded_answer = "Insufficient evidence in the indexed authorities."

    return {
        "answer": grounded_answer,
        "key_findings": verified_findings,
        "legal_principles": verified_principles,
        "authorities": verified_authorities,
        "is_abstained": should_abstain
    }

