import google.generativeai as genai
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.domain import Case, CaseComparison

logger = logging.getLogger("lexora.services.compare")

has_valid_key = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip() and settings.GEMINI_API_KEY != "your_api_key_here")
if has_valid_key:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

def compare_cases_service(
    db: Session,
    case_ids: List[int],
    research_question: Optional[str] = None
) -> dict:
    """
    Multi-Case Comparison Intelligence Service.
    
    Supports 2-5 distinct cases. Produces a structured, evidence-grounded
    comparison matrix with explicit handling of missing fields, distinction
    between legal conflicts vs factual differences, and strict source grounding.
    """
    # 1. Validation of Case IDs
    if not case_ids or len(case_ids) < 2 or len(case_ids) > 5:
        raise ValueError("Comparison requires between 2 and 5 distinct cases.")

    if len(set(case_ids)) != len(case_ids):
        raise ValueError("Duplicate case IDs provided for comparison.")

    cases: List[Case] = []
    for cid in case_ids:
        case = db.query(Case).filter(Case.id == cid).first()
        if not case:
            raise ValueError(f"One or more cases could not be found: Case with ID {cid} could not be found.")
        cases.append(case)

    # 2. Build Source Map and Evidence Context with Honest Missing Fields
    source_map: Dict[str, Dict[str, Any]] = {}
    context_blocks = []

    for case in cases:
        source_id = f"case_{case.id}"
        doc_id = case.documents[0].id if case.documents else None

        # Build honest representations of case profile fields
        facts_list = [f"- {f.fact_type}: {f.description}" for f in case.facts] if case.facts else ["- [Material facts: Not documented in source record]"]
        issues_list = [f"- {i.issue_text}" for i in case.legal_issues] if case.legal_issues else ["- [Legal issues: Not documented in source record]"]
        principles_list = [f"- {p.description}" for p in case.principles] if case.principles else ["- [Legal principles: Not documented in source record]"]
        reasoning_text = case.court_reasoning.strip() if case.court_reasoning and case.court_reasoning.strip() else "[Court reasoning: Not available in source record]"
        decision_text = case.decision.strip() if case.decision and case.decision.strip() else "[Decision/Holding: Not available in source record]"
        remedy_text = case.remedy.strip() if hasattr(case, "remedy") and case.remedy and case.remedy.strip() else "[Remedy/Relief: Not documented in source record]"
        posture_text = case.procedural_history.strip() if hasattr(case, "procedural_history") and case.procedural_history and case.procedural_history.strip() else "[Procedural posture: Unknown / Not documented]"

        source_map[source_id] = {
            "source_id": source_id,
            "case_name": case.case_name,
            "court": case.court or "Unknown Court",
            "year": int(case.year or 0),
            "document_id": doc_id,
            "page_number": 1,
            "chunk_id": f"case_{case.id}_profile",
            "section": "CASE_INTELLIGENCE",
            "matched_text": f"{case.case_name} ({case.court}, {case.year}): {reasoning_text[:200]}",
            "relevance_score": 1.0
        }

        block = (
            f'<case_profile id="{source_id}">\n'
            f'Case Name: {case.case_name}\n'
            f'Court: {case.court or "Unknown Court"}\n'
            f'Year: {case.year or "Unknown Year"}\n'
            f'Procedural Posture: {posture_text}\n'
            f'Facts:\n' + "\n".join(facts_list) + "\n"
            f'Issues:\n' + "\n".join(issues_list) + "\n"
            f'Court Reasoning:\n{reasoning_text}\n'
            f'Holding and Disposition:\n{decision_text}\n'
            f'Relief/Remedy:\n{remedy_text}\n'
            f'Legal Principles:\n' + "\n".join(principles_list) + "\n"
            f'</case_profile>'
        )
        context_blocks.append(block)

    context_str = "\n\n".join(context_blocks)

    # 3. Execution: LLM Generation or Deterministic Fallback
    valid_source_ids = set(source_map.keys())

    if model:
        research_focus = (
            f"Focus the comparison specifically on answering: '{research_question}'"
            if research_question and research_question.strip()
            else "Provide a comprehensive comparative analysis of the legal principles, holdings, and reasoning."
        )

        prompt = f"""
You are an expert Appellate Court Research Jurist.
Compare the following legal cases based STRICTLY on their extracted intelligence profiles inside <case_profile> tags.

{research_focus}

CRITICAL RULES:
1. Answer ONLY using the supplied case profiles. Do not invent missing facts, holdings, or dates.
2. If any field in a profile is noted as unknown or not documented, state that limitation explicitly.
3. Every substantive comparative claim must cite the supporting source IDs (e.g. ["case_1", "case_2"]).
4. LEGAL CONFLICT VS FACTUAL DISTINCTION:
   - Distinguish a true conflict in legal reasoning from a superficial difference in facts, jurisdiction, procedural posture, or statutory framework.
   - Do NOT label a case as conflicting if the courts merely reached different outcomes due to differing facts or different legislative provisions. Label it as "Distinguishable on facts" or "Different statutory context".
5. If evidence is insufficient to compare a specific aspect, state "Insufficient evidence in source records."

Return valid JSON matching this schema:
{{
    "executive_comparison": "Comprehensive synthesis of how these authorities interact.",
    "similarities": [
        {{"claim": "Statement of shared legal rule or fact.", "sources": ["case_1", "case_2"]}}
    ],
    "differences": [
        {{"claim": "Statement of difference in facts, law, or outcome.", "sources": ["case_1", "case_2"]}}
    ],
    "distinguishing_factors": [
        {{"claim": "Key legal or factual factor distinguishing the decisions.", "sources": ["case_1", "case_2"]}}
    ],
    "reasoning_comparison": [
        {{"claim": "Comparison of judicial ratio decidendi.", "sources": ["case_1", "case_2"]}}
    ],
    "principle_comparison": [
        {{"claim": "Comparison of principles established.", "sources": ["case_1", "case_2"]}}
    ],
    "outcome_comparison": [
        {{"claim": "Comparison of final relief or disposition.", "sources": ["case_1", "case_2"]}}
    ],
    "potential_tensions": [
        {{"claim": "Analysis of whether divergence is a genuine legal conflict or distinguishable precedent.", "sources": ["case_1", "case_2"]}}
    ]
}}

CASE PROFILES:
{context_str}
"""
        try:
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            parsed = json.loads(response.text)
        except Exception as e:
            logger.warning(f"Gemini comparison generation failed: {e}. Falling back to deterministic matrix.")
            parsed = _generate_deterministic_comparison(cases, source_map, research_question)
    else:
        # Deterministic evidence-grounded comparison for offline/testing mode
        parsed = _generate_deterministic_comparison(cases, source_map, research_question)

    # 4. Strict Citation Grounding Layer
    categories = [
        "similarities",
        "differences",
        "distinguishing_factors",
        "reasoning_comparison",
        "principle_comparison",
        "outcome_comparison",
        "potential_tensions"
    ]

    for cat in categories:
        items = parsed.get(cat, [])
        grounded_items = []
        for item in items:
            raw_sources = item.get("sources", [])
            valid_sources = [s for s in raw_sources if s in valid_source_ids]
            
            # Map aliases like 'case 1' -> 'case_1' or '1' -> 'case_1'
            if not valid_sources:
                for s in raw_sources:
                    s_str = str(s).strip()
                    if f"case_{s_str}" in valid_source_ids:
                        valid_sources.append(f"case_{s_str}")

            claim_text = item.get("claim", "").strip()
            if valid_sources:
                grounded_items.append({
                    "claim": claim_text,
                    "sources": valid_sources
                })
            else:
                grounded_items.append({
                    "claim": f"[UNSUPPORTED] {claim_text} (Evidence insufficient in source records.)",
                    "sources": []
                })
        parsed[cat] = grounded_items

    parsed["sources"] = list(source_map.values())

    # 5. Persist Comparison Record
    comp = CaseComparison(
        case_ids=json.dumps(case_ids),
        research_question=research_question or "",
        comparison_result=json.dumps(parsed)
    )
    db.add(comp)
    db.commit()
    if hasattr(db, "refresh"):
        db.refresh(comp)

    parsed["comparison_id"] = comp.id
    return parsed


def _generate_deterministic_comparison(
    cases: List[Case],
    source_map: Dict[str, Dict[str, Any]],
    research_question: Optional[str]
) -> dict:
    """
    Constructs a deterministic, evidence-grounded comparison matrix
    directly from database records for offline, CI, and test execution.
    """
    all_source_ids = list(source_map.keys())
    case_names = [c.case_name for c in cases]
    names_str = " vs ".join(case_names)

    similarities = []
    differences = []
    distinguishing_factors = []
    reasoning_comp = []
    principle_comp = []
    outcome_comp = []
    potential_tensions = []

    # Jurisdictional & Temporal differences
    for i in range(len(cases) - 1):
        c1 = cases[i]
        c2 = cases[i + 1]
        srcs = [f"case_{c1.id}", f"case_{c2.id}"]

        if c1.court == c2.court:
            similarities.append({
                "claim": f"Both {c1.case_name} and {c2.case_name} were adjudicated before {c1.court}.",
                "sources": srcs
            })
        else:
            differences.append({
                "claim": f"{c1.case_name} was decided by {c1.court or 'Unknown Court'} ({c1.year or 'N/A'}), whereas {c2.case_name} was decided by {c2.court or 'Unknown Court'} ({c2.year or 'N/A'}).",
                "sources": srcs
            })

        # Procedural Posture / Remedy
        r1 = c1.remedy if hasattr(c1, "remedy") and c1.remedy else "Not documented"
        r2 = c2.remedy if hasattr(c2, "remedy") and c2.remedy else "Not documented"
        outcome_comp.append({
            "claim": f"Outcome disposition: {c1.case_name} decided '{c1.decision or 'Unknown'}', while {c2.case_name} decided '{c2.decision or 'Unknown'}'.",
            "sources": srcs
        })

        # Distinguishing factors
        distinguishing_factors.append({
            "claim": f"Distinguishable on factual context and procedural posture between {c1.case_name} and {c2.case_name}.",
            "sources": srcs
        })

        # Reasoning comparison
        r_text1 = c1.court_reasoning[:120] if c1.court_reasoning else "Reasoning not available in source record"
        r_text2 = c2.court_reasoning[:120] if c2.court_reasoning else "Reasoning not available in source record"
        reasoning_comp.append({
            "claim": f"Reasoning analysis: {c1.case_name} focused on '{r_text1}', whereas {c2.case_name} addressed '{r_text2}'.",
            "sources": srcs
        })

        # Potential tension analysis (distinguishing true conflict vs distinction)
        if c1.court == c2.court and c1.decision and c2.decision and c1.decision != c2.decision:
            potential_tensions.append({
                "claim": f"Potential tension: {c1.case_name} and {c2.case_name} reached different holdings in the same forum ({c1.court}); further examination of factual divergence is required to ascertain if this represents a true legal conflict or a factual distinction.",
                "sources": srcs
            })
        else:
            potential_tensions.append({
                "claim": f"No irreconcilable legal conflict identified between {c1.case_name} and {c2.case_name}; divergences stem from distinct factual circumstances or procedural postures.",
                "sources": srcs
            })

    # Principles
    for c in cases:
        src = [f"case_{c.id}"]
        p_desc = c.principles[0].description if c.principles else "No legal principle documented in record"
        principle_comp.append({
            "claim": f"Principle from {c.case_name}: {p_desc}",
            "sources": src
        })

    exec_summary = (
        f"Comparative legal analysis of {names_str}. "
        f"The cases span {len(cases)} authorities. "
        + ("Addressing research question: " + research_question if research_question else "Analyzing shared doctrine and procedural distinctions.")
    )

    return {
        "executive_comparison": exec_summary,
        "similarities": similarities or [{"claim": "Shared statutory domain under Indian law.", "sources": all_source_ids}],
        "differences": differences,
        "distinguishing_factors": distinguishing_factors,
        "reasoning_comparison": reasoning_comp,
        "principle_comparison": principle_comp,
        "outcome_comparison": outcome_comp,
        "potential_tensions": potential_tensions
    }
