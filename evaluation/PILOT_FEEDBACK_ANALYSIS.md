# LEXORA Pilot Feedback & Issue Triage Report

**Execution Timestamp:** `2026-10-21T10:26:59.775869+00:00`  
**Monitoring Path:** `./storage/monitoring`  
**Status:** **EMPTY STATE — NO ACTIVE PILOT FEEDBACK**

## 1. Executive Summary & Verification Findings

> [!NOTE]
> **No genuine external pilot feedback records currently exist in the monitoring store.**  
> In strict adherence to evaluation integrity principles, **no fictional usage metrics or synthetic user ratings have been generated.**

During Phase 12 acceptance testing, transient test user telemetry and feedback were recorded and subsequently purged during automated verification of GDPR Right-to-be-Forgotten controls (`DELETE /api/evaluation/monitoring/my-events`).

## 2. Issue Taxonomy & Operational Triage Protocol

When external pilot users submit feedback or flag answers, reports are automatically triaged into the following standardized categories:

| Issue Code | Category Description | Operational Remediation Protocol |
| :--- | :--- | :--- |
| `IR_IRRELEVANT_PASSAGE` | Retrieved passage did not address the queried legal issue or statute. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `CLAIM_UNSUPPORTED_BY_PASSAGE` | Generated legal claim lacks evidentiary foundation in cited passage. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `CITATION_METADATA_INVALID` | Citation text or court/year/page metadata does not resolve to an authoritative report. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `CITATION_PASSAGE_UNSUPPORTIVE` | Citation resolves to valid case, but the specific excerpt does not prove the claim. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `ABSTENTION_FALSE_REFUSAL` | System refused to answer despite indexed authoritative evidence. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `ABSTENTION_MISSED_HALLUCINATED_ANSWER` | System generated an answer for an unanswerable or false-premise question. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `COMPARISON_FALSE_CONFLICT` | System reported judicial conflict where precedents are harmonious or distinguishable. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `TIMELINE_DATE_MISATTRIBUTION` | Event date misattributed or confused with judgment pronouncement date. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |
| `PROVIDER_TIMEOUT_OR_DEGRADED` | LLM API provider failure, rate limit, or network disconnection. | Review source document chunking, verify citations against official law reports, and update benchmark suite. |

## 3. Privacy, Anonymization & Retention Controls

- **Zero Query Leakage**: Raw legal queries are masked with `[REDACTED_BY_DEFAULT]` unless explicitly consented to.
- **Tenant Isolation**: Non-admin pilot users can view and delete only their own feedback records.
- **72-Hour Triage SLA**: All practitioner-flagged issues must be acknowledged and triaged within 72 hours.
- **Automated Purging**: Telemetry logs are purged automatically after 30 days (`PILOT_MONITORING_RETENTION_DAYS`).
- **Adjudication Requirement**: User feedback is used to flag potential model failures; it is **never** incorporated directly into ground-truth evaluation datasets without dual review by qualified legal counsel.