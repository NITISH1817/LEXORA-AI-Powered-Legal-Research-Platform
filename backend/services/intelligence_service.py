import google.generativeai as genai
import json
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.domain import (
    Case, CaseFact, LegalIssue, PartyArgument, CaseEvent, 
    ImportantPassage, LegalPrinciple, Citation
)
from backend.config import settings

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash') if settings.GEMINI_API_KEY else None

class CaseIntelligenceEngine:
    
    def __init__(self):
        self.model = model
        
    def analyze_case(self, db: Session, case_id: int):
        if not self.model:
            raise ValueError("Gemini API key is missing.")
            
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise ValueError(f"Case {case_id} not found.")
            
        if case.analysis_status == "COMPLETED":
            return case
            
        case.analysis_status = "PROCESSING"
        db.commit()
        
        try:
            # 1. Fetch full text (or chunks)
            # In a real system, we'd fetch the document chunks from chroma or sqlite
            # and join them. For Lexora Phase 3 prototype, we will simulate the extraction
            # by joining all chunk text.
            chunks = case.documents[0].chunks if case.documents else []
            full_text = "\n".join([c.text for c in chunks])
            
            if not full_text:
                raise ValueError("No text found for case.")
                
            # 2. Prepare Prompt
            prompt = f"""
            You are LEXORA, an expert AI Legal Intelligence Engine.
            Analyze the following legal judgment and extract deeply structured CASE INTELLIGENCE.
            
            RULES:
            1. ONLY extract information actually present in the text.
            2. NEVER hallucinate facts, dates, or citations.
            3. If information is missing, return empty arrays or null.
            4. Keep explanations concise but legally accurate.
            
            JSON SCHEMA EXPECTED:
            {{
                "case_name": "Name of case",
                "case_number": "Case num if found",
                "court": "Court name",
                "judgment_date": "YYYY-MM-DD",
                "legal_topics": "Comma separated topics (e.g. Contract, Damages)",
                "executive_summary": "100-word overview",
                "facts": [
                    {{"fact_type": "Material|Background|Disputed|Undisputed", "description": "fact text", "source_id": "page/para"}}
                ],
                "issues": [
                    {{"issue_text": "Whether..."}}
                ],
                "arguments": {{
                    "Petitioner": [
                        {{"argument_text": "..."}}
                    ],
                    "Respondent": [
                        {{"argument_text": "..."}}
                    ]
                }},
                "reasoning": "Main court reasoning text",
                "decision": "Final decision outcome",
                "principles": [
                    {{"description": "Principle text", "source_passage": "passage", "page_number": 1}}
                ],
                "citations": [
                    {{
                        "case_name": "ABC v XYZ", 
                        "citation_string": "1998 (1) SCC 123",
                        "relationship_type": "CITES|FOLLOWS|DISTINGUISHES|OVERRULES|APPROVES", 
                        "supporting_text": "passage explaining the citation...",
                        "page_number": 1
                    }}
                ],
                "timeline": [
                    {{
                        "event_date": "YYYY-MM-DD (ONLY if exact, else null)",
                        "date_text": "around March 2022 (preserve original text)",
                        "date_precision": "exact|approximate|range|unknown",
                        "event_type": "CONTRACT|JUDGMENT|NOTICE|DISPUTE|APPEAL|OTHER",
                        "title": "Short event title",
                        "description": "Detailed description of the event",
                        "actors": ["Party A", "Court X"],
                        "court": "Court name if applicable",
                        "timeline_type": "FACTUAL|PROCEDURAL",
                        "page_number": 1,
                        "supporting_text": "Exact passage proving this event occurred on this date"
                    }}
                ],
                "important_passages": [
                    {{"category": "REASONING", "text": "passage...", "page_number": 1}}
                ]
            }}
            
            JUDGMENT TEXT:
            {full_text[:50000]} # Limit to 50k chars for safety in sandbox
            """
            
            # 3. Call Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            parsed = json.loads(response.text)
            
            # 4. Save to DB
            case.case_name = parsed.get("case_name", case.case_name)
            case.case_number = parsed.get("case_number", case.case_number)
            case.court = parsed.get("court", case.court)
            # (Date parsing omitted for brevity)
            case.legal_topics = parsed.get("legal_topics", case.legal_topics)
            case.executive_summary = parsed.get("executive_summary")
            case.court_reasoning = parsed.get("reasoning")
            case.decision = parsed.get("decision")
            
            # Clear old nested
            db.query(CaseFact).filter(CaseFact.case_id == case.id).delete()
            db.query(LegalIssue).filter(LegalIssue.case_id == case.id).delete()
            db.query(PartyArgument).filter(PartyArgument.case_id == case.id).delete()
            db.query(CaseEvent).filter(CaseEvent.case_id == case.id).delete()
            db.query(ImportantPassage).filter(ImportantPassage.case_id == case.id).delete()
            db.query(LegalPrinciple).filter(LegalPrinciple.case_id == case.id).delete()
            
            for f in parsed.get("facts", []):
                db.add(CaseFact(case_id=case.id, fact_type=f.get("fact_type","Background"), description=f.get("description"), source_id=f.get("source_id")))
                
            for i in parsed.get("issues", []):
                db.add(LegalIssue(case_id=case.id, issue_text=i.get("issue_text")))
                
            args = parsed.get("arguments", {})
            for party, arr in args.items():
                for a in arr:
                    db.add(PartyArgument(case_id=case.id, party_type=party, argument_text=a.get("argument_text")))
                    
            for p in parsed.get("principles", []):
                db.add(LegalPrinciple(case_id=case.id, description=p.get("description"), source_passage=p.get("source_passage"), page_number=p.get("page_number")))
                
            for ev in parsed.get("timeline", []):
                import json
                actors_json = json.dumps(ev.get("actors", [])) if isinstance(ev.get("actors"), list) else None
                db.add(CaseEvent(
                    case_id=case.id,
                    event_date=ev.get("event_date"),
                    date_text=ev.get("date_text", "Unknown Date"),
                    date_precision=ev.get("date_precision", "unknown"),
                    event_type=ev.get("event_type", "OTHER"),
                    title=ev.get("title", "Event"),
                    description=ev.get("description", ""),
                    actors=actors_json,
                    court=ev.get("court"),
                    timeline_type=ev.get("timeline_type", "FACTUAL"),
                    page_number=ev.get("page_number"),
                    supporting_text=ev.get("supporting_text", "No passage provided"),
                    verification_status="needs_review"
                ))                
            for ip in parsed.get("important_passages", []):
                db.add(ImportantPassage(case_id=case.id, category=ip.get("category", "REASONING"), text=ip.get("text"), page_number=ip.get("page_number")))
                
            from backend.models.domain import CaseCitation
            
            db.query(CaseCitation).filter(CaseCitation.source_case_id == case.id).delete()
            
            for c in parsed.get("citations", []):
                target_name = c.get("case_name")
                
                # Case Resolution
                target_case = None
                if target_name:
                    # Simple heuristic match. In production, use vector similarity or exact alias match
                    target_case = db.query(Case).filter(Case.case_name.ilike(f"%{target_name}%")).first()
                
                db.add(CaseCitation(
                    source_case_id=case.id,
                    target_case_id=target_case.id if target_case else None,
                    target_case_name=target_name,
                    target_citation=c.get("citation_string"),
                    relationship_type=c.get("relationship_type", "CITES"),
                    supporting_text=c.get("supporting_text", "No evidence extracted"),
                    page_number=c.get("page_number")
                ))
                
            case.analysis_status = "COMPLETED"
            db.commit()
            return case
            
        except Exception as e:
            logging.error(f"Analysis failed: {e}")
            case.analysis_status = "FAILED"
            db.commit()
            raise e

intelligence_engine = CaseIntelligenceEngine()
