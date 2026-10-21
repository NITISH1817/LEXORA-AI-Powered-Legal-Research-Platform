"""
LEXORA Legal Annotation & Human Adjudication Workflow System — Phase 14

Enforces strict state transitions, audit logging, and risk prioritization for legal review:
1. States:
   - PENDING_HUMAN_LEGAL_REVIEW: Unreviewed catalog query or expansion item.
   - IN_REVIEW: Assigned to qualified advocate (R1 or R2).
   - APPROVED: Dual-review consensus or senior adjudicator pass.
   - REJECTED: Failed core legal dimension (e.g. flawed holding or ungrounded claim).
   - NEEDS_ADJUDICATION: Reviewer disagreement escalated to Senior Legal Adjudicator.
2. Anti-Fabrication Safeguard:
   - Automated scripts are strictly FORBIDDEN from transitioning items to APPROVED.
   - Valid reviewer credentials / pseudonyms are required for state transitions.
3. Risk Prioritization Engine:
   - Scores legal risk across 8 failure modes (e.g. ratio vs submission, overruling, conflicting precedent).
   - Outputs sorted review queue for qualified legal reviewers.
"""

import os
import json
from enum import Enum
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class ReviewStatus(str, Enum):
    PENDING = "PENDING_HUMAN_LEGAL_REVIEW"
    IN_REVIEW = "IN_REVIEW"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    ANNOTATION_REVIEWED = "ANNOTATION_REVIEWED"
    APPROVED = "APPROVED"
    GOLD_LABEL_APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_ADJUDICATION = "NEEDS_ADJUDICATION"
    DISAGREEMENT_ADJUDICATED = "DISAGREEMENT_ADJUDICATED"


class IllegalStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class AutomatedApprovalForbiddenError(Exception):
    """Raised when automated code attempts to approve a benchmark item without human review."""
    pass


# Legal Risk Weightings based on doctrinal ambiguity and liability impact
RISK_WEIGHTS = {
    "CONFLICT_DISTINCTION": 5.0,
    "CONFLICT_AND_DISTINCTION": 5.0,
    "HOLDING_VS_SUBMISSION": 4.8,
    "ADVERSARIAL": 4.5,
    "STATUTORY_INTERPRETATION": 4.0,
    "MULTI_PASSAGE": 3.8,
    "MULTI_PASSAGE_SYNTHESIS": 3.8,
    "NEGATIVE_CONTROL_ABSTENTION": 3.5,
    "ABSTENTION": 3.5,
    "PRECEDENT_RELATIONSHIP": 3.0,
    "TIMELINE": 2.5,
    "TEMPORAL_PRECISION": 2.5,
    "FACTS_PROCEDURAL": 2.0,
    "HOLDING": 2.0,
    "OCR_NOISE_AND_INCOMPLETE": 2.0,
    "STATUTORY": 2.0,
    "COMPARISON": 3.0
}


def calculate_query_risk_score(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes a risk score (1.0 to 10.0) based on doctrinal complexity,
    bench composition, and potential liability of misattribution.
    """
    category = query.get("category", "GENERAL")
    base_weight = RISK_WEIGHTS.get(category, 2.0)
    
    # Check for landmark Constitution Benches (>=7 judges) or complex precedents
    q_text = (query.get("question") or query.get("query") or "").lower()
    exp_ans = (query.get("expected_answer") or "").lower()
    combined_text = q_text + " " + exp_ans
    
    multipliers = []
    if any(k in combined_text for k in ["overruled", "overruling", "nn global", "interplay", "gopalan", "cooper"]):
        base_weight += 2.0
        multipliers.append("OVERRULED_AUTHORITY_RISK (+2.0)")
    if any(k in combined_text for k in ["ratio", "obiter", "submission", "concurrence", "plurality", "puttaswamy"]):
        base_weight += 1.5
        multipliers.append("SUBMISSION_VS_HOLDING_RISK (+1.5)")
    if any(k in combined_text for k in ["rainbow papers", "paschimanchal", "waterfall", "section 53"]):
        base_weight += 1.5
        multipliers.append("STATUTORY_CONFLICT_RISK (+1.5)")
    if query.get("is_unanswerable") or "ABSTAIN" in query.get("expected_behavior", ""):
        base_weight += 1.0
        multipliers.append("ABSTENTION_BOUNDARY_RISK (+1.0)")
    
    final_score = min(round(base_weight, 2), 10.0)
    
    priority = "PRIORITY_1_CRITICAL" if final_score >= 6.5 else (
        "PRIORITY_2_HIGH" if final_score >= 4.5 else (
            "PRIORITY_3_MEDIUM" if final_score >= 3.0 else "PRIORITY_4_STANDARD"
        )
    )
    
    return {
        "risk_score": final_score,
        "priority_tier": priority,
        "risk_factors": multipliers
    }


class LegalReviewWorkflow:
    def __init__(self, storage_path: str = "evaluation/results/legal_review_records.json"):
        self.storage_path = storage_path
        self.records: Dict[str, Dict[str, Any]] = self._load_records()

    def _load_records(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def save_records(self):
        out_dir = os.path.dirname(self.storage_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

    def transition_state(
        self,
        query_id: str,
        to_status: ReviewStatus,
        reviewer_id: str,
        rationale: str,
        is_automated: bool = False,
        rubric_scores: Optional[Dict[str, bool]] = None,
        source_authority: Optional[str] = None,
        source_location: Optional[str] = None,
        contrary_authority_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a validated state transition with an auditable history trail.
        Strictly forbids automated approval.
        """
        if is_automated and to_status == ReviewStatus.APPROVED:
            raise AutomatedApprovalForbiddenError(
                f"Automated evaluation cannot transition item '{query_id}' to APPROVED. "
                "Review requires qualified practicing advocate or judicial reviewer credentials."
            )
        
        rev_lower = (reviewer_id or "").strip().lower()
        forbidden_substrings = ["bot", "script", "ci", "automated", "runner", "synthetic", "test_bot"]
        if not rev_lower or any(b in rev_lower for b in forbidden_substrings):
            if to_status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
                raise AutomatedApprovalForbiddenError(
                    f"Reviewer identifier '{reviewer_id}' is recognized as an automated agent or synthetic identifier. "
                    "Final legal disposition requires a verified human advocate identifier."
                )

        if to_status in (ReviewStatus.APPROVED, ReviewStatus.REJECTED):
            if not rationale or not rationale.strip():
                raise ValueError(f"Substantive legal rationale is mandatory when transitioning query '{query_id}' to {to_status.value}.")

        current = self.records.get(query_id, {
            "query_id": query_id,
            "status": ReviewStatus.PENDING.value,
            "review_history": []
        })
        from_status = ReviewStatus(current["status"])

        # State transition validation rules
        valid_transitions = {
            ReviewStatus.PENDING: [ReviewStatus.IN_REVIEW],
            ReviewStatus.IN_REVIEW: [
                ReviewStatus.SOURCE_VERIFIED,
                ReviewStatus.ANNOTATION_REVIEWED,
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED,
                ReviewStatus.NEEDS_ADJUDICATION
            ],
            ReviewStatus.SOURCE_VERIFIED: [
                ReviewStatus.ANNOTATION_REVIEWED,
                ReviewStatus.NEEDS_ADJUDICATION,
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED,
                ReviewStatus.IN_REVIEW
            ],
            ReviewStatus.ANNOTATION_REVIEWED: [
                ReviewStatus.APPROVED,
                ReviewStatus.NEEDS_ADJUDICATION,
                ReviewStatus.REJECTED,
                ReviewStatus.IN_REVIEW
            ],
            ReviewStatus.NEEDS_ADJUDICATION: [
                ReviewStatus.DISAGREEMENT_ADJUDICATED,
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED
            ],
            ReviewStatus.DISAGREEMENT_ADJUDICATED: [
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED,
                ReviewStatus.IN_REVIEW
            ],
            ReviewStatus.APPROVED: [ReviewStatus.IN_REVIEW],  # Re-opening allowed upon contestation
            ReviewStatus.REJECTED: [ReviewStatus.IN_REVIEW]
        }

        if to_status not in valid_transitions.get(from_status, []):
            raise IllegalStateTransitionError(
                f"Illegal state transition from {from_status.value} to {to_status.value} for query '{query_id}'."
            )

        timestamp = datetime.now(timezone.utc).isoformat()
        action_entry = {
            "action_id": len(current["review_history"]) + 1,
            "timestamp": timestamp,
            "reviewer_id": reviewer_id,
            "from_status": from_status.value,
            "to_status": to_status.value,
            "rationale": rationale,
            "rubric_scores": rubric_scores or {},
            "source_authority": source_authority or "",
            "source_location": source_location or "",
            "contrary_authority_notes": contrary_authority_notes or ""
        }

        # Track granular lifecycle stages
        current.setdefault("stages", {
            "source_verified": False,
            "annotation_reviewed": False,
            "gold_label_approved": False,
            "disagreement_adjudicated": False
        })
        if to_status == ReviewStatus.SOURCE_VERIFIED:
            current["stages"]["source_verified"] = True
        elif to_status == ReviewStatus.ANNOTATION_REVIEWED:
            current["stages"]["annotation_reviewed"] = True
        elif to_status == ReviewStatus.DISAGREEMENT_ADJUDICATED:
            current["stages"]["disagreement_adjudicated"] = True
        elif to_status == ReviewStatus.APPROVED:
            current["stages"]["gold_label_approved"] = True

        current["status"] = to_status.value
        current["last_updated"] = timestamp
        current["current_reviewer"] = reviewer_id
        current["review_history"].append(action_entry)

        self.records[query_id] = current
        self.save_records()
        return current

    def claim_for_review(self, query_id: str, reviewer_id: str, rationale: str = "Claimed for legal review") -> Dict[str, Any]:
        """Transitions PENDING -> IN_REVIEW."""
        return self.transition_state(query_id, ReviewStatus.IN_REVIEW, reviewer_id, rationale)

    def verify_source(
        self,
        query_id: str,
        reviewer_id: str,
        source_authority: str,
        source_location: str,
        rationale: str = "Source authority text verified against official law reporter"
    ) -> Dict[str, Any]:
        """Transitions IN_REVIEW -> SOURCE_VERIFIED."""
        return self.transition_state(
            query_id,
            ReviewStatus.SOURCE_VERIFIED,
            reviewer_id,
            rationale,
            source_authority=source_authority,
            source_location=source_location
        )

    def review_annotation(
        self,
        query_id: str,
        reviewer_id: str,
        rubric_scores: Dict[str, bool],
        rationale: str
    ) -> Dict[str, Any]:
        """Transitions to ANNOTATION_REVIEWED."""
        return self.transition_state(
            query_id,
            ReviewStatus.ANNOTATION_REVIEWED,
            reviewer_id,
            rationale,
            rubric_scores=rubric_scores
        )

    def request_adjudication(
        self,
        query_id: str,
        reviewer_id: str,
        dispute_rationale: str
    ) -> Dict[str, Any]:
        """Transitions to NEEDS_ADJUDICATION."""
        return self.transition_state(
            query_id,
            ReviewStatus.NEEDS_ADJUDICATION,
            reviewer_id,
            dispute_rationale
        )

    def adjudicate_disagreement(
        self,
        query_id: str,
        adjudicator_id: str,
        rationale: str,
        adjudication_outcome: str = "RESOLUTION_REACHED"
    ) -> Dict[str, Any]:
        """Transitions NEEDS_ADJUDICATION -> DISAGREEMENT_ADJUDICATED."""
        return self.transition_state(
            query_id,
            ReviewStatus.DISAGREEMENT_ADJUDICATED,
            adjudicator_id,
            f"[{adjudication_outcome}] {rationale}"
        )

    def approve_gold_label(
        self,
        query_id: str,
        reviewer_id: str,
        rationale: str,
        source_authority: Optional[str] = None,
        source_location: Optional[str] = None,
        is_automated: bool = False
    ) -> Dict[str, Any]:
        """Final transition to APPROVED (Gold Label Approved). Strictly human-only."""
        return self.transition_state(
            query_id,
            ReviewStatus.APPROVED,
            reviewer_id,
            rationale,
            is_automated=is_automated,
            source_authority=source_authority,
            source_location=source_location
        )

    def reject_annotation(
        self,
        query_id: str,
        reviewer_id: str,
        rationale: str
    ) -> Dict[str, Any]:
        """Transitions to REJECTED."""
        return self.transition_state(
            query_id,
            ReviewStatus.REJECTED,
            reviewer_id,
            rationale
        )

    def get_approved_query_ids(self) -> List[str]:
        """Returns list of query IDs with APPROVED status."""
        return [qid for qid, rec in self.records.items() if rec.get("status") == ReviewStatus.APPROVED.value]

    def get_audit_summary(self, total_queries: int = 160) -> Dict[str, Any]:
        """Calculates audit metrics across all status stages."""
        status_counts = {
            ReviewStatus.PENDING.value: 0,
            ReviewStatus.IN_REVIEW.value: 0,
            ReviewStatus.SOURCE_VERIFIED.value: 0,
            ReviewStatus.ANNOTATION_REVIEWED.value: 0,
            ReviewStatus.APPROVED.value: 0,
            ReviewStatus.REJECTED.value: 0,
            ReviewStatus.NEEDS_ADJUDICATION.value: 0,
            ReviewStatus.DISAGREEMENT_ADJUDICATED.value: 0
        }
        for rec in self.records.values():
            st = rec.get("status", ReviewStatus.PENDING.value)
            status_counts[st] = status_counts.get(st, 0) + 1

        recorded_count = len(self.records)
        status_counts[ReviewStatus.PENDING.value] = max(0, total_queries - recorded_count) + status_counts.get(ReviewStatus.PENDING.value, 0)

        return {
            "total_benchmark_queries": total_queries,
            "recorded_actions_count": sum(len(r.get("review_history", [])) for r in self.records.values()),
            "status_distribution": status_counts,
            "approved_gold_labels_count": status_counts.get(ReviewStatus.APPROVED.value, 0),
            "pending_review_count": status_counts.get(ReviewStatus.PENDING.value, 0),
            "in_review_count": status_counts.get(ReviewStatus.IN_REVIEW.value, 0),
            "adjudication_required_count": status_counts.get(ReviewStatus.NEEDS_ADJUDICATION.value, 0)
        }

    def generate_review_queue(self, benchmark_path: str = "evaluation/datasets/legal_benchmark_v3.json") -> List[Dict[str, Any]]:
        """
        Parses benchmark queries, scores risk, attaches current workflow state,
        and returns a review queue sorted by legal risk descending.
        """
        if not os.path.exists(benchmark_path):
            raise FileNotFoundError(f"Benchmark not found at {benchmark_path}")

        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        queries = data.get("queries", [])
        queue = []

        for q in queries:
            qid = q.get("id") or q.get("query_id", "unknown")
            risk_meta = calculate_query_risk_score(q)
            
            # Retrieve workflow state or default to PENDING
            rec = self.records.get(qid)
            status = rec["status"] if rec else ReviewStatus.PENDING.value
            
            queue.append({
                "query_id": qid,
                "split": q.get("split", "dev"),
                "category": q.get("category", "GENERAL"),
                "question": q.get("question") or q.get("query", ""),
                "required_citations": q.get("required_citations", []),
                "expected_behavior": q.get("expected_behavior", "ANSWER_WITH_CITATION"),
                "status": status,
                "risk_score": risk_meta["risk_score"],
                "priority_tier": risk_meta["priority_tier"],
                "risk_factors": risk_meta["risk_factors"],
                "history_length": len(rec["review_history"]) if rec else 0
            })

        # Sort queue: Highest risk first
        queue.sort(key=lambda x: (x["risk_score"], x["query_id"]), reverse=True)
        return queue

    def export_review_queue_markdown(
        self,
        queue: List[Dict[str, Any]],
        output_path: str = "evaluation/LEGAL_REVIEW_QUEUE.md"
    ) -> str:
        """Exports the prioritized review queue into human-readable Markdown."""
        lines = []
        lines.append("# LEXORA Prioritized Legal Review & Adjudication Queue — Phase 14")
        lines.append("")
        lines.append(f"**Generated Timestamp:** `{datetime.now(timezone.utc).isoformat()}`  ")
        lines.append(f"**Total Benchmark Queries in Queue:** `{len(queue)}`  ")
        lines.append("")

        # Summary breakdown by status and priority
        status_counts = {}
        priority_counts = {}
        for item in queue:
            status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
            priority_counts[item["priority_tier"]] = priority_counts.get(item["priority_tier"], 0) + 1

        lines.append("## 1. Queue Status & Priority Distribution")
        lines.append("")
        lines.append("| Review Status | Item Count | Percentage |")
        lines.append("| :--- | :---: | :---: |")
        for st, c in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| `{st}` | {c} | {c/len(queue)*100:.1f}% |")
        lines.append("")

        lines.append("| Priority Tier | Risk Definition | Item Count | Percentage |")
        lines.append("| :--- | :--- | :---: | :---: |")
        lines.append(f"| `PRIORITY_1_CRITICAL` | Overruled authority, ratio vs submission, insolvency waterfall (Risk >= 6.5) | {priority_counts.get('PRIORITY_1_CRITICAL', 0)} | {priority_counts.get('PRIORITY_1_CRITICAL', 0)/len(queue)*100:.1f}% |")
        lines.append(f"| `PRIORITY_2_HIGH` | Multi-passage plurality, adversarial premise, statutory exceptions (Risk 4.5-6.4) | {priority_counts.get('PRIORITY_2_HIGH', 0)} | {priority_counts.get('PRIORITY_2_HIGH', 0)/len(queue)*100:.1f}% |")
        lines.append(f"| `PRIORITY_3_MEDIUM` | Precedent relationships, negative control boundaries (Risk 3.0-4.4) | {priority_counts.get('PRIORITY_3_MEDIUM', 0)} | {priority_counts.get('PRIORITY_3_MEDIUM', 0)/len(queue)*100:.1f}% |")
        lines.append(f"| `PRIORITY_4_STANDARD` | Direct statutory wording, basic chronological timelines (Risk < 3.0) | {priority_counts.get('PRIORITY_4_STANDARD', 0)} | {priority_counts.get('PRIORITY_4_STANDARD', 0)/len(queue)*100:.1f}% |")
        lines.append("")

        lines.append("## 2. Prioritized Review Queue (Top 30 Critical Items)")
        lines.append("")
        lines.append("Qualified reviewers must claim items starting from `PRIORITY_1_CRITICAL`:")
        lines.append("")
        lines.append("| Priority | Risk Score | Query ID | Category | Question Focus | Required Citation | Review Status |")
        lines.append("| :---: | :---: | :---: | :---: | :--- | :--- | :---: |")

        for item in queue[:30]:
            q_snippet = (item["question"][:65] + "...") if len(item["question"]) > 65 else item["question"]
            cit = item["required_citations"][0] if item["required_citations"] else "N/A"
            lines.append(
                f"| `{item['priority_tier'].split('_')[1]}` | `{item['risk_score']}` | "
                f"`{item['query_id']}` | `{item['category']}` | {q_snippet} | {cit} | `{item['status']}` |"
            )

        lines.append("")
        lines.append("## 3. Human Review Protocol & Escalation Rules")
        lines.append("")
        lines.append("1. **Double-Blind Review**: R1 and R2 must review each item independently without seeing the other reviewer's scores.")
        lines.append("2. **Dispute Escalation**: Any disagreement between R1 and R2 automatically shifts state to `NEEDS_ADJUDICATION`.")
        lines.append("3. **Automated Modification Prohibition**: System automated test runs may read ground truth but cannot modify `review_status`.")
        lines.append("4. **Audit Trail**: All rationale notes, timestamped approvals, and rejections are permanently recorded in `evaluation/results/legal_review_records.json`.")

        content = "\n".join(lines)
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[LEXORA Review Workflow] Priority review queue exported to {output_path}")
        return content

    def export_critical_review_packets(
        self,
        benchmark_path: str = "evaluation/datasets/legal_benchmark_v3.json",
        output_json: str = "evaluation/results/critical_review_packets.json",
        output_md: str = "evaluation/PHASE15_CRITICAL_REVIEW_QUEUE.md"
    ) -> List[Dict[str, Any]]:
        """
        Builds rigorous, authoritative review packets for all 8 Critical-Priority benchmark items.
        Includes authoritative source excerpts, statutory provisions, procedural posture,
        overruling history, and human verification rubrics.
        """
        with open(benchmark_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        queries = {q["id"]: q for q in data.get("queries", [])}
        corpus_list = data.get("corpus") or data.get("passages") or []
        passages = {p["id"]: p for p in corpus_list}

        crit_ids = ["bench_093", "bench_132", "bench_131", "bench_121", "bench_106", "bench_072", "bench_056", "bench_007"]
        
        posture_and_dates = {
            "bench_093": "Gopalan decided May 19, 1950 (AIR 1950 SC 27); Maneka Gandhi decided Jan 25, 1978 ((1978) 1 SCC 248); Puttaswamy decided Aug 24, 2017 ((2017) 10 SCC 1).",
            "bench_132": "Kharak Singh decided Dec 18, 1962 ((1964) 1 SCR 332); Puttaswamy decided Aug 24, 2017 ((2017) 10 SCC 1).",
            "bench_131": "M.P. Sharma decided Mar 15, 1954 (1954 SCR 1077); Puttaswamy decided Aug 24, 2017 ((2017) 10 SCC 1).",
            "bench_121": "Insolvency and Bankruptcy Code enacted 2016; Essar Steel decided Nov 15, 2019 ((2020) 8 SCC 531); Paschimanchal Vidyut decided July 17, 2023 ((2023) 10 SCC 60).",
            "bench_106": "Associate Builders decided Nov 25, 2014 ((2015) 3 SCC 49); Ssangyong Engineering decided May 8, 2019 ((2019) 15 SCC 131); 2015 Amendment Act 3 of 2016.",
            "bench_072": "NN Global (5-Judge) decided Apr 25, 2023 ((2023) 7 SCC 1); In Re Interplay (7-Judge) decided Dec 13, 2023 ((2024) 6 SCC 1).",
            "bench_056": "Puttaswamy (9-Judge) decided Aug 24, 2017 ((2017) 10 SCC 1).",
            "bench_007": "M.P. Sharma (8-Judge, 1954); Kharak Singh (6-Judge, 1962); Puttaswamy (9-Judge, 2017)."
        }

        contrary_authorities = {
            "bench_093": "A.K. Gopalan literal doctrine overruled in Maneka Gandhi. Silo theory between Articles 14, 19, and 21 rejected.",
            "bench_132": "Majority in Kharak Singh rejecting privacy right expressly overruled; dissent of Subba Rao, J. affirmed.",
            "bench_131": "M.P. Sharma observation that Indian Constitution excludes right to privacy expressly overruled.",
            "bench_121": "State Tax Officer v. Rainbow Papers (2022) distinguished/clarified by Paschimanchal Vidyut (2023) regarding priority under Section 53.",
            "bench_106": "Associate Builders expansive patent illegality ground curtailed following 2015 Amendment inserting Section 34(2A).",
            "bench_072": "NN Global (2023) 5-judge bench overruled; SMS Tea and Vidya Drolia stamping holdings modified/clarified.",
            "bench_056": "Executive surveillance without statutory authorization is ultra vires; proportionality requires legitimate aim and least intrusive means.",
            "bench_007": "M.P. Sharma and Kharak Singh overruled on privacy exclusion."
        }

        known_uncertainties = {
            "bench_093": "Scope of proportionality vs American substantive due process. Application of proportionality across statutory vs executive actions.",
            "bench_132": "Extents to which physical domiciliary surveillance differs from digital metadata surveillance under post-Puttaswamy jurisprudence.",
            "bench_131": "Interplay between Article 20(3) right against self-incrimination and Article 21 digital device password disclosure compelled by law enforcement.",
            "bench_121": "Tension between statutory security interests created by state tax laws and Section 53 non-obstante priority over state taxes.",
            "bench_106": "Threshold between patent illegality on face of award vs impermissible reappreciation of evidence by Section 34 court.",
            "bench_072": "Procedure when stamp duty deficit is evident on certified copy produced before Section 11 referral court vs original document.",
            "bench_056": "Balancing national security surveillance exceptions against lack of independent judicial oversight mechanisms.",
            "bench_007": "Application of horizontal privacy obligations against private corporate data aggregators."
        }

        packets = []
        for qid in crit_ids:
            q = queries.get(qid, {})
            risk_meta = calculate_query_risk_score(q)
            rec = self.records.get(qid, {})
            status = rec.get("status", ReviewStatus.PENDING.value)

            target_ids = q.get("relevant_chunk_ids", {})
            if isinstance(target_ids, dict):
                target_chunk_ids = list(target_ids.keys())
            elif isinstance(target_ids, list):
                target_chunk_ids = target_ids
            else:
                target_chunk_ids = []

            chunk_details = []
            for cid in target_chunk_ids:
                p = passages.get(cid, {})
                meta_p = p.get("metadata", {})
                chunk_details.append({
                    "chunk_id": cid,
                    "case_name": meta_p.get("case_name") or p.get("source_document") or cid,
                    "citation": meta_p.get("citation") or p.get("case_citation") or "Official Reporter",
                    "court": meta_p.get("court") or "Supreme Court of India",
                    "year": meta_p.get("year") or 2020,
                    "excerpt": p.get("text", "")
                })

            packet = {
                "query_id": qid,
                "question": q.get("question", ""),
                "split": q.get("split", "dev"),
                "category": q.get("category", "CRITICAL"),
                "risk_score": risk_meta["risk_score"],
                "priority_tier": "PRIORITY_1_CRITICAL",
                "risk_factors": risk_meta["risk_factors"],
                "current_status": status,
                "legal_domain": q.get("subject_area", "Constitutional / Commercial Jurisprudence"),
                "court_level": q.get("court_level", "Supreme Court of India"),
                "jurisdiction": "Supreme Court of India / Indian Union",
                "procedural_posture_and_judgment_date": posture_and_dates.get(qid, "Supreme Court of India judgment"),
                "proposed_expected_answer": q.get("expected_answer", ""),
                "required_citations": q.get("required_citations", []),
                "authoritative_sources": chunk_details,
                "potential_contrary_or_overruling_authorities": contrary_authorities.get(qid, "See relevant Constitution Bench ruling"),
                "abstention_expectation": "MUST NOT ABSTAIN — Indexed controlling authorities substantiate ratio.",
                "known_uncertainties_and_reviewer_questions": known_uncertainties.get(qid, "Doctrinal nuances between bench compositions."),
                "human_verification_checklist": {
                    "source_verified": False,
                    "holding_accurately_extracted": False,
                    "ratio_distinguished_from_obiter": False,
                    "overruled_authorities_flagged": False,
                    "procedural_posture_verified": False,
                    "gold_label_approved": False
                }
            }
            packets.append(packet)

        # Write JSON
        out_json_dir = os.path.dirname(output_json)
        if out_json_dir:
            os.makedirs(out_json_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(packets, f, indent=2)

        # Write Markdown Report
        md_lines = []
        md_lines.append("# LEXORA Critical Legal Review Packets — Phase 15")
        md_lines.append("")
        md_lines.append(f"**Execution Timestamp:** `{datetime.now(timezone.utc).isoformat()}`  ")
        md_lines.append(f"**Critical Priority Items (Tier 1):** `{len(packets)}`  ")
        md_lines.append(f"**Mandatory Legal Standard:** Independent advocate verification against official law reporters (SCR, SCC, AIR).  ")
        md_lines.append("")
        md_lines.append("> [!IMPORTANT]")
        md_lines.append("> **Anti-Fabrication Notice:** Automated tests and synthetic test suites are **FORBIDDEN** from approving these items. ")
        md_lines.append("> These review packets are prepared for qualified practicing advocates to perform dual human review and adjudication.")
        md_lines.append("")

        for i, pkt in enumerate(packets, 1):
            md_lines.append(f"## Review Packet {i}: `{pkt['query_id']}` ({pkt['priority_tier']}, Risk Score: {pkt['risk_score']})")
            md_lines.append("")
            md_lines.append(f"- **Legal Question:** *{pkt['question']}*")
            md_lines.append(f"- **Split:** `{pkt['split']}` | **Category:** `{pkt['category']}` | **Status:** `{pkt['current_status']}`")
            md_lines.append(f"- **Domain & Jurisdiction:** {pkt['legal_domain']} — {pkt['jurisdiction']}")
            md_lines.append(f"- **Procedural Posture & Dates:** {pkt['procedural_posture_and_judgment_date']}")
            md_lines.append(f"- **Required Citations:** {', '.join(pkt['required_citations'])}")
            md_lines.append(f"- **Proposed Expected Answer:** {pkt['proposed_expected_answer']}")
            md_lines.append(f"- **Contrary / Overruling Authority Notes:** {pkt['potential_contrary_or_overruling_authorities']}")
            md_lines.append(f"- **Abstention Expectation:** {pkt['abstention_expectation']}")
            md_lines.append(f"- **Known Legal Uncertainties:** {pkt['known_uncertainties_and_reviewer_questions']}")
            md_lines.append("")
            md_lines.append("### Authoritative Indexed Passages")
            for chunk in pkt["authoritative_sources"]:
                md_lines.append(f"- **Chunk ID:** `{chunk['chunk_id']}` | **Authority:** *{chunk['case_name']}* ({chunk['citation']})")
                md_lines.append(f"  > \"{chunk['excerpt'][:280]}...\"")
            md_lines.append("")
            md_lines.append("### Advocate Verification Rubric & Checklist")
            md_lines.append("- [ ] **Source Authenticity:** Passage text corresponds verbatim to official report.")
            md_lines.append("- [ ] **Controlling Ratio:** Holding reflects majority opinion, not concurring or dissenting obiter.")
            md_lines.append("- [ ] **Precedent Currency:** Overruling or distinguishing authorities are accurately tracked.")
            md_lines.append("- [ ] **Evidentiary Support:** Ground-truth claims are 100% substantiated by cited passages.")
            md_lines.append("- [ ] **Adjudication Disposition:** Approved by Primary Advocate (R1) / Secondary Advocate (R2).")
            md_lines.append("")
            md_lines.append("---")
            md_lines.append("")

        out_md_dir = os.path.dirname(output_md)
        if out_md_dir:
            os.makedirs(out_md_dir, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"[LEXORA Review Workflow] Exported {len(packets)} critical review packets to {output_json} and {output_md}")
        return packets

    def export_review_status_audit(
        self,
        output_json: str = "evaluation/results/review_status_audit.json",
        output_md: str = "evaluation/results/review_status_audit.md",
        total_queries: int = 160
    ) -> Dict[str, Any]:
        """Exports complete audit report on current benchmark human review and adjudication state."""
        summary = self.get_audit_summary(total_queries=total_queries)

        out_dir = os.path.dirname(output_json)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        md_lines = [
            "# LEXORA Human Legal Review & Adjudication Status Audit",
            "",
            f"**Audit Execution Timestamp:** `{datetime.now(timezone.utc).isoformat()}`  ",
            f"**Total Benchmark Catalog Queries:** `{summary['total_benchmark_queries']}`  ",
            f"**Recorded Review Actions in Audit Log:** `{summary['recorded_actions_count']}`  ",
            f"**Authoritative Approved Gold Labels:** `{summary['approved_gold_labels_count']}`  ",
            "",
            "## 1. Status Distribution Table",
            "",
            "| Review Lifecycle State | Query Count | Percentage | Operational Significance |",
            "| :--- | :---: | :---: | :--- |",
        ]
        status_descriptions = {
            ReviewStatus.PENDING.value: "Unreviewed items awaiting assignment to advocate.",
            ReviewStatus.IN_REVIEW.value: "Claimed and currently under substantive review.",
            ReviewStatus.SOURCE_VERIFIED.value: "Source judgment/statute verified against law report.",
            ReviewStatus.ANNOTATION_REVIEWED.value: "Proposed question and expected answer evaluated.",
            ReviewStatus.APPROVED.value: "Dual-reviewed and approved as authoritative gold label.",
            ReviewStatus.REJECTED.value: "Rejected due to misattributed ratio, erroneous statute, or hallucination.",
            ReviewStatus.NEEDS_ADJUDICATION.value: "Reviewer disagreement requiring Senior Legal Adjudicator.",
            ReviewStatus.DISAGREEMENT_ADJUDICATED.value: "Disagreement resolved by senior adjudicator pass."
        }
        for st, count in summary["status_distribution"].items():
            pct = count / summary["total_benchmark_queries"] * 100
            desc = status_descriptions.get(st, "Active workflow state.")
            md_lines.append(f"| `{st}` | {count} | {pct:.1f}% | {desc} |")

        out_md_dir = os.path.dirname(output_md)
        if out_md_dir:
            os.makedirs(out_md_dir, exist_ok=True)
        with open(output_md, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        print(f"[LEXORA Review Workflow] Status audit written to {output_json} and {output_md}")
        return summary


def run_generate_review_queue():
    workflow = LegalReviewWorkflow()
    queue = workflow.generate_review_queue()
    workflow.export_review_queue_markdown(queue)
    
    # Save machine-readable JSON queue
    json_path = "evaluation/results/legal_review_queue.json"
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)
    print(f"[LEXORA Review Workflow] Machine-readable queue saved to {json_path}")

    # Export Critical Review Packets (Task 2)
    workflow.export_critical_review_packets()

    # Export Status Audit (Task 1 & Task 3)
    workflow.export_review_status_audit()


if __name__ == "__main__":
    run_generate_review_queue()
