"""
Legal Structure Detection Service — Phase 10
Detects legal document sections using regex + keyword heuristics.
No LLM required — pure pattern matching for speed and reliability.

Supported sections:
  BACKGROUND, FACTS, PLEADINGS, PLAINTIFF_ARGUMENTS, DEFENDANT_ARGUMENTS,
  ISSUES, EVIDENCE, ANALYSIS, REASONING, FINDINGS, JUDGMENT, ORDER,
  CONCLUSION, PROCEDURAL_HISTORY, OTHER

Design notes:
- Not every judgment contains all sections — absent sections are simply not returned.
- Detection is probabilistic (confidence 0.0–1.0).
- Overlapping sections resolved by taking the highest-confidence match per page.
"""

import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger("lexora.legal_structure")

# ---------------------------------------------------------------------------
# Section keyword patterns — ordered by specificity (more specific first)
# ---------------------------------------------------------------------------

SECTION_PATTERNS: List[Dict] = [
    {
        "section_type": "JUDGMENT",
        "patterns": [
            r"\b(JUDGMENT|JUDGEMENT|FINAL\s+ORDER|JUDGMENT\s+AND\s+ORDER)\b",
            r"\bIT\s+IS\s+HEREBY\s+(ORDERED|ADJUDGED|DECREED)\b",
        ],
        "confidence": 0.90,
    },
    {
        "section_type": "ORDER",
        "patterns": [
            r"\b(ORDER|INTERIM\s+ORDER|EX\s+PARTE\s+ORDER|CONSENT\s+ORDER)\b",
            r"\bTHE\s+COURT\s+ORDERS?\b",
        ],
        "confidence": 0.85,
    },
    {
        "section_type": "FACTS",
        "patterns": [
            r"\b(FACTS\s+OF\s+THE\s+CASE|STATEMENT\s+OF\s+FACTS|MATERIAL\s+FACTS|UNDISPUTED\s+FACTS)\b",
            r"\bFACTS\b",
            r"\bBRIEF\s+FACTS\b",
        ],
        "confidence": 0.80,
    },
    {
        "section_type": "ISSUES",
        "patterns": [
            r"\b(ISSUES?\s+FOR\s+DETERMINATION|QUESTIONS?\s+OF\s+LAW|LEGAL\s+ISSUES?|POINTS?\s+OF\s+DETERMINATION)\b",
            r"\bISSUES?\b",
        ],
        "confidence": 0.85,
    },
    {
        "section_type": "PLAINTIFF_ARGUMENTS",
        "patterns": [
            r"\b(PETITIONER.S\s+ARGUMENTS?|PLAINTIFF.S\s+ARGUMENTS?|APPELLANT.S\s+ARGUMENTS?|ARGUMENTS?\s+BY\s+THE\s+PETITIONER|SUBMISSIONS?\s+OF\s+THE\s+PETITIONER)\b",
            r"\bPETITIONER.S\s+SUBMISSIONS?\b",
        ],
        "confidence": 0.85,
    },
    {
        "section_type": "DEFENDANT_ARGUMENTS",
        "patterns": [
            r"\b(RESPONDENT.S\s+ARGUMENTS?|DEFENDANT.S\s+ARGUMENTS?|ARGUMENTS?\s+BY\s+THE\s+RESPONDENT|SUBMISSIONS?\s+OF\s+THE\s+RESPONDENT)\b",
            r"\bRESPONDENT.S\s+SUBMISSIONS?\b",
        ],
        "confidence": 0.85,
    },
    {
        "section_type": "PLEADINGS",
        "patterns": [
            r"\b(PLEADINGS?|WRITTEN\s+STATEMENT|PLAINT|PRAYER|RELIEF\s+SOUGHT)\b",
        ],
        "confidence": 0.75,
    },
    {
        "section_type": "EVIDENCE",
        "patterns": [
            r"\b(EVIDENCE|EXHIBITS?|DOCUMENTARY\s+EVIDENCE|ORAL\s+EVIDENCE|WITNESSES?)\b",
        ],
        "confidence": 0.75,
    },
    {
        "section_type": "ANALYSIS",
        "patterns": [
            r"\b(ANALYSIS|LEGAL\s+ANALYSIS|DISCUSSION|OUR\s+ANALYSIS)\b",
        ],
        "confidence": 0.80,
    },
    {
        "section_type": "REASONING",
        "patterns": [
            r"\b(REASONING|COURT.S\s+REASONING|RATIO\s+DECIDENDI|OBSERVATIONS?\s+OF\s+THE\s+COURT)\b",
        ],
        "confidence": 0.80,
    },
    {
        "section_type": "FINDINGS",
        "patterns": [
            r"\b(FINDINGS?|FINDINGS?\s+OF\s+FACT|FINDINGS?\s+AND\s+CONCLUSIONS?|OUR\s+FINDINGS?)\b",
        ],
        "confidence": 0.80,
    },
    {
        "section_type": "CONCLUSION",
        "patterns": [
            r"\b(CONCLUSION|CONCLUDING\s+REMARKS?|SUMMARY\s+OF\s+CONCLUSIONS?)\b",
        ],
        "confidence": 0.75,
    },
    {
        "section_type": "PROCEDURAL_HISTORY",
        "patterns": [
            r"\b(PROCEDURAL\s+HISTORY|CASE\s+HISTORY|BACKGROUND\s+AND\s+PROCEDURE|PRIOR\s+PROCEEDINGS?)\b",
        ],
        "confidence": 0.80,
    },
    {
        "section_type": "BACKGROUND",
        "patterns": [
            r"\b(BACKGROUND|INTRODUCTION|CONTEXT|PREAMBLE)\b",
        ],
        "confidence": 0.70,
    },
]

# Compile patterns once for performance
_COMPILED: List[Dict] = []
for sp in SECTION_PATTERNS:
    _COMPILED.append({
        "section_type": sp["section_type"],
        "patterns": [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in sp["patterns"]],
        "confidence": sp["confidence"],
    })


# ---------------------------------------------------------------------------
# Core Detection Function
# ---------------------------------------------------------------------------

def detect_legal_sections(pages: List[Dict]) -> List[Dict]:
    """
    Scan pages and return detected sections.

    Args:
        pages: List of {page_number, text, word_count, has_text} dicts

    Returns:
        List of {section_type, confidence, start_page, end_page, page_number}
    """
    detections: List[Dict] = []

    # Per-page detection
    page_section_map: Dict[int, Dict] = {}  # page_number → best detection

    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text") or ""
        if not text.strip():
            continue

        # Check each section pattern against this page
        best: Optional[Dict] = None

        for sp in _COMPILED:
            for pattern in sp["patterns"]:
                if pattern.search(text):
                    if best is None or sp["confidence"] > best["confidence"]:
                        best = {
                            "section_type": sp["section_type"],
                            "confidence": sp["confidence"],
                            "page_number": page_num,
                        }
                    break  # matched this section type, try next

        if best:
            page_section_map[page_num] = best

    # Convert page-level detections to range-based section spans
    if not page_section_map:
        return []

    sorted_pages = sorted(page_section_map.keys())
    section_spans: List[Dict] = []
    current_section: Optional[Dict] = None
    current_start: Optional[int] = None

    for page_num in sorted_pages:
        detection = page_section_map[page_num]
        if current_section is None:
            current_section = detection
            current_start = page_num
        elif detection["section_type"] != current_section["section_type"]:
            section_spans.append({
                "section_type": current_section["section_type"],
                "confidence": current_section["confidence"],
                "start_page": current_start,
                "end_page": page_num - 1,
            })
            current_section = detection
            current_start = page_num

    # Add the last section
    if current_section and current_start is not None:
        last_page = sorted_pages[-1]
        section_spans.append({
            "section_type": current_section["section_type"],
            "confidence": current_section["confidence"],
            "start_page": current_start,
            "end_page": last_page,
        })

    logger.info("Legal section detection found %d sections", len(section_spans))
    return section_spans


def get_section_for_page(page_num: int, sections: List[Dict]) -> str:
    """
    Return the section type for a given page number.
    Falls back to 'OTHER' if no section detected.
    """
    for sec in sections:
        start = sec.get("start_page", 0)
        end = sec.get("end_page", float("inf"))
        if start <= page_num <= end:
            return sec["section_type"]
    return "OTHER"
