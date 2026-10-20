"""
LEXORA Human Legal Review Submission & Adjudication CLI Tool — Phase 16

Provides an auditable, interactive, and batch command-line workflow for licensed legal
advocates and judicial reviewers to inspect review packets, record source verification,
evaluate candidate annotations, resolve disagreements, and approve/reject gold labels.

Key Safeguards:
1. Automated approval forbidden: Rejects bot, script, or CI runner IDs.
2. Distinct non-interchangeable states:
   PENDING -> IN_REVIEW -> SOURCE_VERIFIED -> ANNOTATION_REVIEWED -> APPROVED / REJECTED
   NEEDS_ADJUDICATION -> DISAGREEMENT_ADJUDICATED -> APPROVED
3. Substantive legal rationale is mandatory for final dispositions.
4. Append-only audit history with timestamps and reviewer provenance.
5. JSON packet import for external practitioner review packets.
"""

import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add workspace root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.review_workflow import (
    LegalReviewWorkflow,
    ReviewStatus,
    IllegalStateTransitionError,
    AutomatedApprovalForbiddenError,
    calculate_query_risk_score,
)


def format_packet_display(packet: Dict[str, Any]) -> str:
    """Formats a review packet into human-readable text for terminal inspection."""
    lines = []
    lines.append("=" * 80)
    lines.append(f"LEGAL REVIEW PACKET: {packet.get('query_id')} [{packet.get('priority_tier', 'STANDARD')}]")
    lines.append(f"Risk Score: {packet.get('risk_score', 'N/A')} | Current Status: {packet.get('current_status', packet.get('status', 'PENDING'))}")
    lines.append("=" * 80)
    lines.append(f"QUESTION: {packet.get('question')}")
    lines.append(f"DOMAIN: {packet.get('legal_domain', packet.get('category', 'Constitutional'))}")
    lines.append(f"JURISDICTION: {packet.get('jurisdiction', 'Supreme Court of India')}")
    lines.append(f"PROCEDURAL POSTURE & DATES: {packet.get('procedural_posture_and_judgment_date', 'N/A')}")
    lines.append(f"REQUIRED CITATIONS: {', '.join(packet.get('required_citations', []))}")
    lines.append("")
    lines.append("PROPOSED EXPECTED ANSWER:")
    lines.append(f"  {packet.get('proposed_expected_answer', packet.get('expected_answer', 'N/A'))}")
    lines.append("")
    lines.append("CONTRARY / OVERRULING PRECEDENT NOTES:")
    lines.append(f"  {packet.get('potential_contrary_or_overruling_authorities', 'None documented')}")
    lines.append("")
    lines.append("KNOWN UNCERTAINTIES & REVIEWER QUESTIONS:")
    lines.append(f"  {packet.get('known_uncertainties_and_reviewer_questions', 'Standard doctrinal verification')}")
    lines.append("")
    lines.append("INDEXED AUTHORITATIVE PASSAGES:")
    sources = packet.get("authoritative_sources", [])
    if not sources and "authoritative_passages" in packet:
        sources = packet["authoritative_passages"]
    for idx, chunk in enumerate(sources, 1):
        lines.append(f"  [{idx}] Chunk ID: {chunk.get('chunk_id')}")
        lines.append(f"      Authority: {chunk.get('case_name')} ({chunk.get('citation')})")
        lines.append(f"      Court / Year: {chunk.get('court')} ({chunk.get('year')})")
        lines.append(f"      Excerpt: \"{chunk.get('excerpt', chunk.get('text', ''))[:300]}...\"")
    lines.append("-" * 80)
    lines.append("ADVOCATE VERIFICATION CHECKLIST:")
    lines.append("  [ ] 1. Source authenticity: Checked against official reporter (SCR, SCC, AIR).")
    lines.append("  [ ] 2. Controlling holding: Ratio accurately isolated from concurring/dissenting obiter.")
    lines.append("  [ ] 3. Precedent currency: Subsequent overruling or distinguishing authorities verified.")
    lines.append("  [ ] 4. Grounding: Proposed claims are 100% substantiated by cited passages.")
    lines.append("=" * 80)
    return "\n".join(lines)


def process_import_packet(workflow: LegalReviewWorkflow, packet_path: str) -> Dict[str, Any]:
    """
    Imports and applies an external advocate's structured review packet.
    Validates required fields, reviewer credentials, and state progression.
    """
    if not os.path.exists(packet_path):
        raise FileNotFoundError(f"Review packet file not found at: {packet_path}")

    with open(packet_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Required field validation
    required_keys = ["query_id", "reviewer_id", "decision", "rationale"]
    for k in required_keys:
        if k not in data or not str(data[k]).strip():
            raise ValueError(f"Import packet missing required field: '{k}'")

    qid = data["query_id"]
    rev_id = data["reviewer_id"]
    decision = str(data["decision"]).upper()
    rationale = data["rationale"].strip()

    # Step 1: Claim if pending
    current = workflow.records.get(qid)
    curr_status = current.get("status") if current else ReviewStatus.PENDING.value

    if curr_status == ReviewStatus.PENDING.value:
        workflow.claim_for_review(qid, rev_id, rationale="Claimed via imported review packet")

    # Step 2: Source verification if provided
    source_auth = data.get("source_authority", "Law Reporter Checked")
    source_loc = data.get("source_location", "Official Judgment Transcript")
    if data.get("source_verified", True):
        workflow.verify_source(
            qid, rev_id,
            source_authority=source_auth,
            source_location=source_loc,
            rationale=data.get("source_verification_notes", "Source authority and date verified")
        )

    # Step 3: Annotation review rubric
    rubric = data.get("rubric_scores", {
        "ratio_accuracy": True,
        "citation_support": True,
        "procedural_fidelity": True
    })
    workflow.review_annotation(
        qid, rev_id,
        rubric_scores=rubric,
        rationale=data.get("annotation_notes", "Annotation and citation support reviewed against evidence")
    )

    # Step 4: Final disposition
    if decision in ("APPROVED", "GOLD_LABEL_APPROVED"):
        rec = workflow.approve_gold_label(
            qid, rev_id,
            rationale=rationale,
            source_authority=source_auth,
            source_location=source_loc
        )
    elif decision == "REJECTED":
        rec = workflow.reject_annotation(qid, rev_id, rationale=rationale)
    elif decision in ("NEEDS_ADJUDICATION", "ESCALATE"):
        rec = workflow.request_adjudication(qid, rev_id, dispute_rationale=rationale)
    else:
        raise ValueError(f"Unknown decision '{decision}'. Expected APPROVED, REJECTED, or NEEDS_ADJUDICATION.")

    return rec


def main():
    parser = argparse.ArgumentParser(description="LEXORA Human Legal Review Submission & Adjudication CLI")
    parser.add_argument("--storage", default="evaluation/results/legal_review_records.json", help="Path to review records JSON")
    
    # Query / queue actions
    parser.add_argument("--list-queue", action="store_true", help="List prioritized review queue")
    parser.add_argument("--tier", choices=["ALL", "CRITICAL", "HIGH", "MEDIUM", "STANDARD"], default="ALL", help="Filter queue by priority tier")
    parser.add_argument("--status-filter", choices=["ALL", "PENDING", "IN_REVIEW", "SOURCE_VERIFIED", "ANNOTATION_REVIEWED", "APPROVED", "REJECTED"], default="ALL")
    parser.add_argument("--inspect", metavar="QUERY_ID", help="Inspect detailed review packet for a query")
    
    # Workflow transitions
    parser.add_argument("--claim", metavar="QUERY_ID", help="Claim query for review")
    parser.add_argument("--verify-source", metavar="QUERY_ID", help="Record source verification for query")
    parser.add_argument("--review-annotation", metavar="QUERY_ID", help="Record annotation and citation review")
    parser.add_argument("--approve", metavar="QUERY_ID", help="Approve gold label for query (requires human credentials)")
    parser.add_argument("--reject", metavar="QUERY_ID", help="Reject annotation for query")
    parser.add_argument("--request-adjudication", metavar="QUERY_ID", help="Escalate to senior legal adjudication")
    parser.add_argument("--adjudicate", metavar="QUERY_ID", help="Senior adjudicator resolves disagreement")
    
    # Reviewer metadata & inputs
    parser.add_argument("--reviewer", help="Authorized Reviewer ID / Bar Enrollment No.")
    parser.add_argument("--adjudicator", help="Senior Legal Adjudicator ID")
    parser.add_argument("--rationale", help="Mandatory substantive legal rationale")
    parser.add_argument("--source-auth", default="Official Supreme Court Reporter (SCR/SCC/AIR)", help="Primary source authority identifier")
    parser.add_argument("--source-loc", default="Majority Opinion Transcript", help="Page / paragraph reference")
    parser.add_argument("--ratio-ok", action="store_true", default=True, help="Rubric: Controlling ratio accurately isolated")
    parser.add_argument("--citation-ok", action="store_true", default=True, help="Rubric: Required citations exist and substantiate claim")
    parser.add_argument("--procedural-ok", action="store_true", default=True, help="Rubric: Procedural posture and date accurate")
    parser.add_argument("--decision", choices=["APPROVED", "REJECTED"], default="APPROVED", help="Adjudication final decision")
    
    # Import / export actions
    parser.add_argument("--import-packet", metavar="PATH_TO_JSON", help="Import external advocate signed review packet")
    parser.add_argument("--audit-status", action="store_true", help="Display current audit summary of benchmark review")
    
    args = parser.parse_args()

    workflow = LegalReviewWorkflow(storage_path=args.storage)

    # 1. Audit status
    if args.audit_status:
        summary = workflow.get_audit_summary()
        print("\n" + "=" * 60)
        print("LEXORA BENCHMARK HUMAN LEGAL REVIEW AUDIT")
        print("=" * 60)
        print(f"Total Benchmark Queries: {summary['total_benchmark_queries']}")
        print(f"Recorded Review Actions: {summary['recorded_actions_count']}")
        print(f"Approved Gold Labels:    {summary['approved_gold_labels_count']}")
        print(f"Pending Advocate Review: {summary['pending_review_count']}")
        print(f"Under Active Review:     {summary['in_review_count']}")
        print(f"Adjudication Required:   {summary['adjudication_required_count']}")
        print("\nStatus Distribution:")
        for st, cnt in summary["status_distribution"].items():
            pct = (cnt / summary['total_benchmark_queries']) * 100
            print(f"  - {st:<28}: {cnt:>3} ({pct:>5.1f}%)")
        print("=" * 60 + "\n")
        return

    # 2. List queue
    if args.list_queue:
        queue = workflow.generate_review_queue()
        tier_map = {
            "CRITICAL": "PRIORITY_1_CRITICAL",
            "HIGH": "PRIORITY_2_HIGH",
            "MEDIUM": "PRIORITY_3_MEDIUM",
            "STANDARD": "PRIORITY_4_STANDARD"
        }
        filtered = queue
        if args.tier != "ALL":
            target_tier = tier_map.get(args.tier, args.tier)
            filtered = [q for q in filtered if q["priority_tier"] == target_tier]
        if args.status_filter != "ALL":
            filtered = [q for q in filtered if q["status"] == args.status_filter]

        print(f"\nShowing {len(filtered)} queries (Tier: {args.tier}, Status: {args.status_filter}):")
        print(f"{'Query ID':<12} | {'Tier':<20} | {'Risk':<5} | {'Status':<28} | {'Question':<40}")
        print("-" * 115)
        for q in filtered:
            q_short = (q["question"][:37] + "...") if len(q["question"]) > 40 else q["question"]
            print(f"{q['query_id']:<12} | {q['priority_tier']:<20} | {q['risk_score']:<5} | {q['status']:<28} | {q_short}")
        print("-" * 115 + "\n")
        return

    # 3. Inspect packet
    if args.inspect:
        packets = workflow.export_critical_review_packets()
        matching = [p for p in packets if p["query_id"] == args.inspect]
        if matching:
            print(format_packet_display(matching[0]))
        else:
            # Check general queue
            queue = workflow.generate_review_queue()
            q_match = [q for q in queue if q["query_id"] == args.inspect]
            if q_match:
                print(format_packet_display(q_match[0]))
            else:
                print(f"Error: Query '{args.inspect}' not found in benchmark catalog.")
        return

    # 4. Import packet
    if args.import_packet:
        try:
            rec = process_import_packet(workflow, args.import_packet)
            print(f"\n[SUCCESS] Imported review packet for '{rec['query_id']}'. Status updated to: {rec['status']}")
            print(f"Reviewer: {rec['current_reviewer']} | Timestamp: {rec['last_updated']}\n")
        except Exception as e:
            print(f"\n[ERROR] Failed to import review packet: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 5. Claim query
    if args.claim:
        if not args.reviewer:
            print("Error: --reviewer <id> is required to claim an item for review.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.claim_for_review(args.claim, args.reviewer, rationale=args.rationale or "Claimed for legal review")
            print(f"\n[SUCCESS] Query '{args.claim}' claimed by '{args.reviewer}'. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Claim failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 6. Verify source
    if args.verify_source:
        if not args.reviewer:
            print("Error: --reviewer <id> is required for source verification.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.verify_source(
                args.verify_source,
                args.reviewer,
                source_authority=args.source_auth,
                source_location=args.source_loc,
                rationale=args.rationale or "Source authority and holding excerpt verified against official report"
            )
            print(f"\n[SUCCESS] Source verified for '{args.verify_source}'. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Source verification failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 7. Review annotation
    if args.review_annotation:
        if not args.reviewer:
            print("Error: --reviewer <id> is required for annotation review.", file=sys.stderr)
            sys.exit(1)
        if not args.rationale:
            print("Error: --rationale <text> is mandatory for annotation review.", file=sys.stderr)
            sys.exit(1)
        try:
            rubric = {
                "ratio_accuracy": args.ratio_ok,
                "citation_support": args.citation_ok,
                "procedural_fidelity": args.procedural_ok
            }
            rec = workflow.review_annotation(args.review_annotation, args.reviewer, rubric_scores=rubric, rationale=args.rationale)
            print(f"\n[SUCCESS] Annotation reviewed for '{args.review_annotation}'. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Annotation review failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 8. Approve gold label
    if args.approve:
        if not args.reviewer:
            print("Error: --reviewer <id> is required for gold label approval.", file=sys.stderr)
            sys.exit(1)
        if not args.rationale:
            print("Error: --rationale <text> is mandatory for gold label approval.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.approve_gold_label(
                args.approve,
                args.reviewer,
                rationale=args.rationale,
                source_authority=args.source_auth,
                source_location=args.source_loc
            )
            print(f"\n[SUCCESS] Gold label APPROVED for '{args.approve}' by '{args.reviewer}'. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Approval rejected: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 9. Reject annotation
    if args.reject:
        if not args.reviewer:
            print("Error: --reviewer <id> is required for rejection.", file=sys.stderr)
            sys.exit(1)
        if not args.rationale:
            print("Error: --rationale <text> is mandatory for rejection.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.reject_annotation(args.reject, args.reviewer, rationale=args.rationale)
            print(f"\n[SUCCESS] Annotation REJECTED for '{args.reject}'. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Rejection failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 10. Request adjudication
    if args.request_adjudication:
        if not args.reviewer:
            print("Error: --reviewer <id> is required to request adjudication.", file=sys.stderr)
            sys.exit(1)
        if not args.rationale:
            print("Error: --rationale <dispute_notes> is required to request adjudication.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.request_adjudication(args.request_adjudication, args.reviewer, dispute_rationale=args.rationale)
            print(f"\n[SUCCESS] Query '{args.request_adjudication}' escalated. Status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Escalation failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    # 11. Adjudicate
    if args.adjudicate:
        if not args.adjudicator:
            print("Error: --adjudicator <id> is required for senior adjudication.", file=sys.stderr)
            sys.exit(1)
        if not args.rationale:
            print("Error: --rationale <text> is mandatory for adjudication.", file=sys.stderr)
            sys.exit(1)
        try:
            rec = workflow.adjudicate_disagreement(
                args.adjudicate,
                args.adjudicator,
                rationale=args.rationale,
                adjudication_outcome=f"RESOLVED_{args.decision}"
            )
            if args.decision == "APPROVED":
                rec = workflow.approve_gold_label(
                    args.adjudicate,
                    args.adjudicator,
                    rationale=f"Post-adjudication approval: {args.rationale}"
                )
            print(f"\n[SUCCESS] Senior adjudication completed for '{args.adjudicate}'. Final status: {rec['status']}\n")
        except Exception as e:
            print(f"\n[ERROR] Adjudication failed: {e}\n", file=sys.stderr)
            sys.exit(1)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
