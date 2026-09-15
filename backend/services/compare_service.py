import google.generativeai as genai
import json
import logging
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models.domain import Case, CaseComparison
from typing import List

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash') if settings.GEMINI_API_KEY else None

def compare_cases_service(db: Session, case_ids: List[int], research_question: str = None) -> dict:
    if len(case_ids) < 2 or len(case_ids) > 5:
        raise ValueError("Comparison requires between 2 and 5 cases.")
        
    if not model:
        raise ValueError("Gemini API key is missing.")

    cases = []
    for cid in case_ids:
        case = db.query(Case).filter(Case.id == cid).first()
        if case:
            cases.append(case)
            
    if len(cases) != len(case_ids):
        raise ValueError("One or more cases could not be found.")

    # Build prompt context
    context_str = "CASE INTELLIGENCE PROFILES:\n\n"
    source_map = {}
    
    for case in cases:
        source_id = f"case_{case.id}"
        source_map[source_id] = {
            "source_id": source_id,
            "case_name": case.case_name,
            "court": case.court,
            "year": case.year,
            "document_id": case.documents[0].id if case.documents else None,
            "page_number": 1,
            "chunk_id": "profile",
            "matched_text": f"Extracted Intelligence Profile for {case.case_name}"
        }
        
        context_str += f"--- [{source_id}] {case.case_name} ---\n"
        context_str += f"Court: {case.court}, Year: {case.year}\n"
        context_str += "Facts:\n"
        for f in case.facts:
            context_str += f"- {f.fact_type}: {f.description}\n"
        context_str += "Issues:\n"
        for i in case.legal_issues:
            context_str += f"- {i.issue_text}\n"
        context_str += f"Reasoning:\n{case.court_reasoning}\n"
        context_str += f"Decision:\n{case.decision}\n"
        context_str += "Principles:\n"
        for p in case.principles:
            context_str += f"- {p.description}\n"
        context_str += "\n"

    research_focus = f"Focus the comparison on this specific research question: '{research_question}'" if research_question else "Provide a comprehensive legal comparison of these cases."

    prompt = f"""
    You are an expert Appellate Court Judge and Legal Researcher.
    Compare the following legal cases based STRICTLY on their extracted intelligence.
    
    {research_focus}
    
    RULES:
    1. Answer ONLY using the supplied evidence. Do not hallucinate facts or principles.
    2. Cite supporting sources using the provided source IDs (e.g., ["case_1", "case_2"]).
    3. DETECT POTENTIAL TENSION: Do not automatically assume cases conflict. If reasoning appears different, label it as a "potential tension", "distinguishable", or "different factual context" unless it is explicitly an overturn/conflict.
    4. If evidence is insufficient for a claim, do not make the claim.
    
    JSON SCHEMA EXPECTED:
    {{
        "executive_comparison": "Overall synthesis (approx 150 words).",
        "similarities": [
            {{"claim": "Both cases involved X", "sources": ["case_1", "case_2"]}}
        ],
        "differences": [
            {{"claim": "Case 1 involved Y while Case 2 involved Z", "sources": ["case_1", "case_2"]}}
        ],
        "distinguishing_factors": [
            {{"claim": "The duration of delay distinguishes the cases.", "sources": ["case_1", "case_2"]}}
        ],
        "reasoning_comparison": [
            {{"claim": "Both courts applied the same test but diverged on...", "sources": ["case_1", "case_2"]}}
        ],
        "principle_comparison": [
            {{"claim": "Case 1 established A, Case 2 qualified A by adding B.", "sources": ["case_1", "case_2"]}}
        ],
        "outcome_comparison": [
            {{"claim": "Case 1 allowed the claim, Case 2 rejected it.", "sources": ["case_1", "case_2"]}}
        ],
        "potential_tensions": [
            {{"claim": "There is potential tension in how the courts viewed X...", "sources": ["case_1", "case_2"]}}
        ]
    }}
    
    {context_str}
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        parsed = json.loads(response.text)
    except Exception as e:
        logging.error(f"Gemini generation failed: {e}")
        raise ValueError("Failed to generate response from Gemini API.")
        
    # Validation step: Ensure sources are real
    valid_ids = set(source_map.keys())
    for category in ["similarities", "differences", "distinguishing_factors", "reasoning_comparison", "principle_comparison", "outcome_comparison", "potential_tensions"]:
        for item in parsed.get(category, []):
            item["sources"] = [s for s in item.get("sources", []) if s in valid_ids]

    parsed["sources"] = list(source_map.values())
    
    # Save comparison history
    comp = CaseComparison(
        case_ids=json.dumps(case_ids),
        research_question=research_question,
        comparison_result=json.dumps(parsed)
    )
    db.add(comp)
    db.commit()
    
    parsed["comparison_id"] = comp.id
    
    return parsed
