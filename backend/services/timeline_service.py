import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from dateutil import parser as date_parser

from backend.models.domain import Case, CaseEvent, DocumentChunk
from backend.schemas.domain import DatePrecision, TimelineCategory, AttributionStatus

logger = logging.getLogger("lexora.services.timeline")

# -----------------------------------------------------------------------------
# Regex Patterns for Date & Precision Detection
# -----------------------------------------------------------------------------

# Exact Date Patterns (e.g. 15 May 2024, 15th May, 2024, 2024-05-15, 15/05/2024, 15-05-2024)
EXACT_DATE_REGEX = re.compile(
    r"\b(\d{1,2}(?:st|nd|rd|th)?[\s\/\-\.,]+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2})[\s\/\-\.,]+\d{4})\b"
    r"|\b(\d{4}-\d{2}-\d{2})\b"
    r"|\b((?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\b",
    re.IGNORECASE
)

# Approximate Date Patterns (e.g. around March 2022, circa 2015, in or about 2018, early 2020, mid-2019)
APPROXIMATE_DATE_REGEX = re.compile(
    r"\b(?:around|circa|about|in or around|in or about|sometime in|approximately|early|mid|late)[\s\-]+"
    r"(?:(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+)?\d{4}\b"
    r"|\bin the year \d{4}\b"
    r"|\bcirca \d{4}\b",
    re.IGNORECASE
)

# Date Range Patterns (e.g. between 2018 and 2020, from 12 January 2019 to 15 March 2019, during 2015-2017)
RANGE_DATE_REGEX = re.compile(
    r"\b(?:between|from)\s+(.+?)\s+(?:and|to)\s+(.+?)(?=[,\.;]|\s+when|\s+the\s+parties|\s+an?\s+|$)"
    r"|\bduring\s+(?:the\s+period\s+)?(\d{4})\s*[-–]\s*(\d{4})\b",
    re.IGNORECASE
)

# Relative / Undated Expressions (e.g. several years later, subsequently, thereafter, at all material times)
RELATIVE_DATE_REGEX = re.compile(
    r"\b(several years later|subsequently|thereafter|at all material times|shortly afterwards|at a later stage|later on|eventually|in due course)\b",
    re.IGNORECASE
)

# Allegation / Disputed Indicators
ALLEGATION_REGEX = re.compile(
    r"\b(alleged|allegation|claimed|claim of|contended|contention|submitted that|averred|pleaded|asserted by|purported|disputed by|petitioner argued|respondent argued|submission of)\b",
    re.IGNORECASE
)

# Procedural Event Keywords
PROCEDURAL_KEYWORDS = re.compile(
    r"\b(petition|appeal|suit|application|hearing|order|judgment|decree|writ|stay|injunction|arbitration|award|notice|filing|summons|tribunal|bench|slp)\b",
    re.IGNORECASE
)


# -----------------------------------------------------------------------------
# Date Parsing & Precision Classification
# -----------------------------------------------------------------------------

def parse_date_expression(raw_text: str) -> Tuple[Optional[str], str, str, Optional[str], Optional[str]]:
    """
    Parses a date expression and classifies its precision.
    Returns: (event_date, date_text, date_precision, start_date, end_date)
    """
    cleaned = raw_text.strip()
    
    # 1. Check Date Range
    range_match = RANGE_DATE_REGEX.search(cleaned)
    if range_match:
        if range_match.group(3) and range_match.group(4):
            # Form: during 2015-2017
            s_year, e_year = range_match.group(3), range_match.group(4)
            return (None, cleaned, "range", s_year, e_year)
        elif range_match.group(1) and range_match.group(2):
            s_str, e_str = range_match.group(1).strip(), range_match.group(2).strip()
            # Attempt to parse start and end dates
            s_dt = _try_parse_iso(s_str) or s_str
            e_dt = _try_parse_iso(e_str) or e_str
            return (None, cleaned, "range", s_dt, e_dt)

    # 2. Check Approximate Dates
    if APPROXIMATE_DATE_REGEX.search(cleaned):
        # Strict rule: Never infer an exact calendar day from an approximate phrase
        return (None, cleaned, "approximate", None, None)

    # 3. Check Relative / Undated Expressions
    if RELATIVE_DATE_REGEX.search(cleaned):
        # Strict rule: Do not manufacture a calendar date for relative expressions
        return (None, cleaned, "unknown", None, None)

    # 4. Check Exact Dates
    exact_match = EXACT_DATE_REGEX.search(cleaned)
    if exact_match:
        matched_str = exact_match.group(0)
        iso_date = _try_parse_iso(matched_str)
        if iso_date:
            return (iso_date, cleaned, "exact", None, None)

    # 5. Bare Year fallback (e.g. '2020') - Treat as approximate, NOT exact day!
    bare_year_match = re.fullmatch(r"\b(19\d\d|20\d\d)\b", cleaned)
    if bare_year_match:
        return (None, f"in the year {cleaned}", "approximate", None, None)

    # 6. Default to unknown
    return (None, cleaned or "Unknown Date", "unknown", None, None)


def _try_parse_iso(date_str: str) -> Optional[str]:
    """Helper to convert varied date string formats into YYYY-MM-DD."""
    try:
        clean_str = date_str.strip()
        # If it's a bare 4-digit year, preserve it without filling in current month/day
        if re.fullmatch(r"^(19\d\d|20\d\d)$", clean_str):
            return clean_str
        # Strip ordinal suffixes: 1st, 2nd, 3rd, 4th -> 1, 2, 3, 4
        clean_str = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", clean_str)
        dt = date_parser.parse(clean_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Grounding & Fabrication Checks
# -----------------------------------------------------------------------------

def validate_date_grounding(
    event_date: Optional[str],
    date_text: str,
    date_precision: str,
    supporting_text: str
) -> Tuple[Optional[str], str, str, str]:
    """
    Verifies that a date claimed by an extractor or LLM is genuinely grounded in the source passage.
    Returns: (validated_event_date, validated_date_text, validated_precision, verification_status)
    """
    if not supporting_text or not supporting_text.strip():
        # Missing supporting text cannot verify any exact date
        return (None, date_text, "unknown", "unsupported")

    supp_lower = supporting_text.lower()
    
    # 1. If source passage contains approximate qualifiers, demote exact dates
    if APPROXIMATE_DATE_REGEX.search(supp_lower):
        if date_precision.lower() == "exact" or event_date is not None:
            logger.info(f"Demoting claimed exact date {event_date} to approximate based on source passage.")
            return (None, date_text, "approximate", "demoted_to_approximate")

    # 2. If source passage contains relative expressions only
    if RELATIVE_DATE_REGEX.search(supp_lower) and not EXACT_DATE_REGEX.search(supp_lower):
        if date_precision.lower() in ["exact", "range"]:
            return (None, date_text, "unknown", "unsupported")

    # 3. For claimed exact dates, verify date numbers and month appear in supporting passage
    if date_precision.lower() == "exact" and event_date:
        parts = event_date.split("-")
        if len(parts) == 3:
            year, month_num, day = parts
            month_names = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
            month_idx = int(month_num) - 1
            month_abbrev = month_names[month_idx] if 0 <= month_idx < 12 else ""

            # Check if year is in text
            year_in_text = year in supp_lower
            day_in_text = day.lstrip("0") in supp_lower or day in supp_lower
            month_in_text = (month_abbrev in supp_lower) or (month_num in supp_lower)

            if not (year_in_text and (day_in_text or month_in_text)):
                logger.warning(f"Claimed exact date {event_date} not grounded in passage: '{supporting_text[:80]}...'")
                return (None, date_text, "unknown", "unsupported")

    return (event_date, date_text, date_precision.lower(), "verified")


def distinguish_from_judgment_date(
    event_date: Optional[str],
    date_text: str,
    event_type: str,
    judgment_date_str: Optional[str],
    supporting_text: str
) -> Tuple[Optional[str], str, str]:
    """
    Ensures that substantive factual events (contracts, breaches, tenders) are not
    conflated with the judgment delivery date.
    """
    if not judgment_date_str or not event_date:
        return (event_date, date_text, "verified")

    # If event is not a judgment or final order, but carries the exact judgment date:
    if event_type.upper() not in ["JUDGMENT", "ORDER", "DECREE", "DECISION"]:
        if event_date == judgment_date_str:
            # Check if the passage actually speaks of judgment delivery
            if not any(k in supporting_text.lower() for k in ["delivered", "bench", "pronounced", "disposed"]):
                # Conflated date detected!
                logger.warning(f"Event '{event_type}' was erroneously assigned judgment date {judgment_date_str}.")
                return (None, "Date not stated in event passage", "unsupported")

    return (event_date, date_text, "verified")


def resolve_relative_date(
    relative_expr: str,
    anchor_date_str: Optional[str],
    supporting_text: str
) -> Tuple[Optional[str], str, str]:
    """
    Resolves relative date expressions only when an exact anchor date is available and mathematically sound.
    Example: 'two weeks after 1 January 2020' -> 2020-01-15.
    Returns: (resolved_date, precision, explanation)
    """
    if not anchor_date_str:
        return (None, "unknown", "Anchor date not provided")

    anchor_iso = _try_parse_iso(anchor_date_str)
    if not anchor_iso:
        return (None, "unknown", "Anchor date could not be parsed to calendar day")

    try:
        anchor_dt = datetime.strptime(anchor_iso, "%Y-%m-%d")
        
        # Check patterns like: X days/weeks/months/years after/later
        days_match = re.search(r"(\d+)\s+days?\s+(?:after|later)", relative_expr, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
            res_dt = anchor_dt + timedelta(days=days)
            return (res_dt.strftime("%Y-%m-%d"), "exact", f"Resolved {days} days after {anchor_iso}")

        weeks_match = re.search(r"(\d+)\s+weeks?\s+(?:after|later)", relative_expr, re.IGNORECASE)
        if weeks_match:
            weeks = int(weeks_match.group(1))
            res_dt = anchor_dt + timedelta(weeks=weeks)
            return (res_dt.strftime("%Y-%m-%d"), "exact", f"Resolved {weeks} weeks after {anchor_iso}")

    except Exception as e:
        logger.debug(f"Relative date resolution error: {e}")

    return (None, "unknown", "Relative expression too vague for deterministic resolution")


# -----------------------------------------------------------------------------
# Allegation & Factual / Procedural Separation
# -----------------------------------------------------------------------------

def detect_attribution(
    title: str,
    description: str,
    supporting_text: str
) -> Tuple[bool, str]:
    """
    Determines whether an event represents a party's allegation or an established finding.
    Returns: (is_allegation: bool, attribution_status: str)
    """
    combined = f"{title} {description} {supporting_text}".lower()
    
    if ALLEGATION_REGEX.search(combined):
        if "dispute" in combined or "contended" in combined or "denied" in combined:
            return (True, AttributionStatus.DISPUTED.value)
        return (True, AttributionStatus.ALLEGATION.value)
    
    return (False, AttributionStatus.ESTABLISHED.value)


def classify_timeline_type(event_type: str, title: str, description: str) -> str:
    """
    Separates events into FACTUAL, PROCEDURAL, or STATUTORY.
    """
    combined = f"{event_type} {title} {description}".lower()
    
    if "section" in combined or "act" in combined or "amendment" in combined or "gazette" in combined:
        if "came into force" in combined or "statutory notification" in combined:
            return TimelineCategory.STATUTORY.value
            
    if PROCEDURAL_KEYWORDS.search(combined):
        return TimelineCategory.PROCEDURAL.value
        
    return TimelineCategory.FACTUAL.value


# -----------------------------------------------------------------------------
# Chunk Deduplication Across Overlapping Chunks
# -----------------------------------------------------------------------------

def deduplicate_timeline_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merges duplicate events occurring across overlapping document chunks.
    Preserves all chunk and page references without creating duplicate entries.
    """
    deduped: List[Dict[str, Any]] = []
    seen_signatures: Dict[str, int] = {} # signature -> index in deduped

    for ev in events:
        t_type = ev.get("timeline_type", "FACTUAL")
        date_key = ev.get("event_date") or ev.get("date_text", "unknown").lower().strip()
        
        # Normalize title key using basic tokens
        title_words = [w for w in re.sub(r"[^\w\s]", "", ev.get("title", "").lower()).split() if len(w) > 3]
        title_key = " ".join(sorted(title_words[:4]))
        
        sig = f"{t_type}::{date_key}::{title_key}"

        if sig in seen_signatures:
            existing_idx = seen_signatures[sig]
            existing = deduped[existing_idx]
            
            # Merge supporting text if the new one adds information
            new_supp = ev.get("supporting_text", "")
            if new_supp and new_supp not in existing.get("supporting_text", ""):
                existing["supporting_text"] = f"{existing.get('supporting_text', '')} | [Chunk Ref]: {new_supp}"
            
            # Aggregate chunk IDs
            c_id = ev.get("source_chunk_id")
            if c_id and c_id not in str(existing.get("source_chunk_id", "")):
                existing["source_chunk_id"] = f"{existing.get('source_chunk_id', '')}, {c_id}".strip(", ")
                
            # Prefer non-null page number
            if not existing.get("page_number") and ev.get("page_number"):
                existing["page_number"] = ev.get("page_number")
        else:
            seen_signatures[sig] = len(deduped)
            deduped.append(dict(ev))

    return deduped


# -----------------------------------------------------------------------------
# Chronological Sorting with Mixed Precision
# -----------------------------------------------------------------------------

def sort_timeline_events(events: List[Any]) -> Tuple[List[Any], List[Any]]:
    """
    Sorts events chronologically when valid date precision allows it.
    Events with UNKNOWN date precision are partitioned into undated_events
    to prevent false chronological implications.
    """
    dated = []
    undated = []

    for ev in events:
        # Check precision
        precision = getattr(ev, "date_precision", None) or (ev.get("date_precision") if isinstance(ev, dict) else "unknown")
        precision = str(precision).lower()
        
        event_date = getattr(ev, "event_date", None) or (ev.get("event_date") if isinstance(ev, dict) else None)
        date_text = getattr(ev, "date_text", "") or (ev.get("date_text") if isinstance(ev, dict) else "")

        if precision == "unknown" or (event_date is None and not re.search(r"\b(19\d\d|20\d\d)\b", date_text)):
            undated.append(ev)
        else:
            dated.append(ev)

    def sort_key(item):
        e_date = getattr(item, "event_date", None) or (item.get("event_date") if isinstance(item, dict) else None)
        if e_date:
            return e_date
        # Approximate fallback anchor
        d_txt = getattr(item, "date_text", "") or (item.get("date_text") if isinstance(item, dict) else "")
        year_m = re.search(r"\b(19\d\d|20\d\d)\b", d_txt)
        if year_m:
            return f"{year_m.group(1)}-01-01"
        return "9999-12-31"

    sorted_dated = sorted(dated, key=sort_key)
    return sorted_dated, undated


# -----------------------------------------------------------------------------
# Case Timeline Service Provider
# -----------------------------------------------------------------------------

def get_case_timeline_data(case_id: int, db: Session) -> Dict[str, Any]:
    """
    Retrieves and formats complete timeline intelligence for a case.
    Separates factual and procedural events, applies grounded sorting,
    and partitions undated events.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case with ID {case_id} not found.")

    events = db.query(CaseEvent).filter(CaseEvent.case_id == case_id).all()
    
    # Sort dated and undated events
    dated_events, undated_events = sort_timeline_events(events)
    all_sorted = dated_events + undated_events

    factual = [e for e in all_sorted if e.timeline_type == "FACTUAL"]
    procedural = [e for e in all_sorted if e.timeline_type == "PROCEDURAL"]

    return {
        "case_id": case_id,
        "factual_events": factual,
        "procedural_events": procedural,
        "events": all_sorted,
        "undated_events": undated_events
    }
