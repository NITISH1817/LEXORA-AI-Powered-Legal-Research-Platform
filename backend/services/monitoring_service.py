"""
LEXORA Privacy-Safe Pilot Monitoring Service — Phase 11

Provides privacy-preserving audit logging and telemetry for limited pilot deployment:
1. Records request metadata (latency, candidate count, citation validation status, abstention).
2. NEVER logs API keys, passwords, bearer tokens, or full document text.
3. Raw legal queries are REDACTED by default (opt-in configuration with retention limit).
4. Enforces strict user isolation: users can inspect/delete only their own events.
5. Administrative summary aggregates telemetry without cross-user leakage.
6. Automated retention policy cleanup.
"""

import os
import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from backend.config import settings

# Sensitive patterns that must never appear in telemetry logs
SENSITIVE_PATTERNS = [
    re.compile(r'(?:api[_-]?key|secret|password|bearer|auth|token)\s*[:=]\s*[^\s,;]+', re.IGNORECASE),
    re.compile(r'Bearer\s+[A-Za-z0-9\-_\.=]+', re.IGNORECASE),
    re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')  # Email redaction
]


def sanitize_text(text: str) -> str:
    """Removes sensitive keys, passwords, and tokens from any logged string."""
    if not text:
        return ""
    sanitized = text
    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SENSITIVE]", sanitized)
    return sanitized


class PilotMonitoringService:
    def __init__(self, monitoring_dir: Optional[str] = None):
        self.monitoring_dir = monitoring_dir or settings.PILOT_MONITORING_DIR
        os.makedirs(self.monitoring_dir, exist_ok=True)

    def _get_events_file(self, date_str: Optional[str] = None) -> str:
        d = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(self.monitoring_dir, f"pilot_events_{d}.jsonl")

    def _get_feedback_file(self, date_str: Optional[str] = None) -> str:
        d = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return os.path.join(self.monitoring_dir, f"pilot_feedback_{d}.jsonl")

    def record_event(
        self,
        user_id: int,
        request_id: Optional[str] = None,
        app_version: str = "2.0.0",
        retrieval_mode: str = "hybrid_rrf",
        candidate_count: int = 0,
        latency_ms: float = 0.0,
        citations_validated: bool = False,
        citations_count: int = 0,
        abstained: bool = False,
        status: str = "SUCCESS",
        failure_category: str = "NONE",
        query_text: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Records a telemetry event. Returns the record dict if enabled, None if disabled.
        Strict privacy controls are enforced.
        """
        if not settings.PILOT_MONITORING_ENABLED:
            return None

        req_id = request_id or str(uuid.uuid4())
        timestamp_utc = datetime.now(timezone.utc).isoformat()

        # Handle query retention privacy
        if settings.PILOT_MONITORING_LOG_QUERIES and query_text:
            safe_query = sanitize_text(query_text[:500])
        else:
            safe_query = "[REDACTED_BY_DEFAULT]"

        # Sanitize any custom metadata
        safe_meta = {}
        if custom_metadata:
            for k, v in custom_metadata.items():
                if any(sec in k.lower() for sec in ["key", "pass", "token", "auth", "secret"]):
                    continue
                safe_meta[k] = sanitize_text(str(v)) if isinstance(v, str) else v

        record = {
            "event_id": str(uuid.uuid4()),
            "request_id": req_id,
            "timestamp_utc": timestamp_utc,
            "app_version": app_version,
            "user_id": user_id,
            "retrieval_mode": retrieval_mode,
            "candidate_count": candidate_count,
            "latency_ms": round(latency_ms, 2),
            "citations_validated": citations_validated,
            "citations_count": citations_count,
            "abstained": abstained,
            "status": status,
            "failure_category": failure_category,
            "query_summary": safe_query,
            "metadata": safe_meta
        }

        file_path = self._get_events_file()
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return record

    def record_feedback(
        self,
        request_id: str,
        user_id: int,
        rating: Optional[int] = None,
        review_status: str = "PENDING",
        review_notes: Optional[str] = None,
        flag_reason: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Records user feedback or legal expert review outcome for a specific request.
        """
        if not settings.PILOT_MONITORING_ENABLED:
            return None

        record = {
            "feedback_id": str(uuid.uuid4()),
            "request_id": request_id,
            "user_id": user_id,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "rating": rating,
            "review_status": review_status,
            "review_notes": sanitize_text(review_notes or ""),
            "flag_reason": sanitize_text(flag_reason or "")
        }

        file_path = self._get_feedback_file()
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        return record

    def get_user_events(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieves telemetry records belonging strictly to user_id (tenant isolation).
        """
        if not settings.PILOT_MONITORING_ENABLED or not os.path.exists(self.monitoring_dir):
            return []

        user_events = []
        files = sorted(os.listdir(self.monitoring_dir), reverse=True)
        for fname in files:
            if not fname.startswith("pilot_events_") or not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(self.monitoring_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            ev = json.loads(line)
                            if ev.get("user_id") == user_id:
                                user_events.append(ev)
                                if len(user_events) >= limit:
                                    return user_events
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

        return user_events

    def get_admin_summary(self) -> Dict[str, Any]:
        """
        Aggregates system-wide pilot telemetry into high-level metrics for administrators.
        Does NOT expose raw individual query contents or user associations.
        """
        if not settings.PILOT_MONITORING_ENABLED or not os.path.exists(self.monitoring_dir):
            return {"status": "MONITORING_DISABLED_OR_EMPTY", "total_requests": 0}

        total_requests = 0
        total_latency = 0.0
        total_abstentions = 0
        total_citations_validated = 0
        failure_counts = {}
        unique_users = set()

        files = sorted(os.listdir(self.monitoring_dir))
        for fname in files:
            if not fname.startswith("pilot_events_") or not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(self.monitoring_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            ev = json.loads(line)
                            total_requests += 1
                            total_latency += ev.get("latency_ms", 0.0)
                            if ev.get("abstained"):
                                total_abstentions += 1
                            if ev.get("citations_validated"):
                                total_citations_validated += 1
                            fc = ev.get("failure_category", "NONE")
                            failure_counts[fc] = failure_counts.get(fc, 0) + 1
                            unique_users.add(ev.get("user_id"))
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

        # Aggregated Feedback Stats
        feedback_count = 0
        ratings = []
        flagged_count = 0
        for fname in files:
            if not fname.startswith("pilot_feedback_") or not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(self.monitoring_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            fb = json.loads(line)
                            feedback_count += 1
                            r = fb.get("rating")
                            if r is not None:
                                ratings.append(r)
                            if fb.get("review_status") == "FLAGGED" or fb.get("flag_reason"):
                                flagged_count += 1
                        except json.JSONDecodeError:
                            continue
            except OSError:
                continue

        return {
            "monitoring_enabled": settings.PILOT_MONITORING_ENABLED,
            "query_logging_enabled": settings.PILOT_MONITORING_LOG_QUERIES,
            "retention_days": settings.PILOT_MONITORING_RETENTION_DAYS,
            "total_requests": total_requests,
            "active_pilot_users_count": len(unique_users),
            "average_latency_ms": round(total_latency / max(total_requests, 1), 2),
            "total_abstentions": total_abstentions,
            "abstention_rate": round(total_abstentions / max(total_requests, 1), 4),
            "citations_validated_total": total_citations_validated,
            "failure_taxonomy_distribution": failure_counts,
            "feedback_summary": {
                "total_feedback_submissions": feedback_count,
                "average_rating": round(sum(ratings) / max(len(ratings), 1), 2) if ratings else None,
                "flagged_issues_count": flagged_count
            }
        }

    def delete_user_records(self, user_id: int) -> int:
        """
        Deletes all telemetry events and feedback records belonging to a user (GDPR compliance).
        Returns the number of deleted records.
        """
        if not os.path.exists(self.monitoring_dir):
            return 0

        deleted_count = 0
        files = os.listdir(self.monitoring_dir)

        for fname in files:
            if not (fname.startswith("pilot_events_") or fname.startswith("pilot_feedback_")) or not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(self.monitoring_dir, fname)
            kept_lines = []
            file_modified = False

            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if data.get("user_id") == user_id:
                                deleted_count += 1
                                file_modified = True
                            else:
                                kept_lines.append(line)
                        except json.JSONDecodeError:
                            kept_lines.append(line)

                if file_modified:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.writelines(kept_lines)
            except OSError:
                continue

        return deleted_count

    def cleanup_expired_records(self, retention_days: Optional[int] = None) -> int:
        """
        Deletes log files older than the retention period.
        """
        days = retention_days if retention_days is not None else settings.PILOT_MONITORING_RETENTION_DAYS
        if not os.path.exists(self.monitoring_dir):
            return 0

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        deleted_files = 0

        for fname in os.listdir(self.monitoring_dir):
            match = re.search(r'(\d{4}-\d{2}-\d{2})', fname)
            if match:
                try:
                    file_date = datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if file_date < cutoff:
                        os.remove(os.path.join(self.monitoring_dir, fname))
                        deleted_files += 1
                except ValueError:
                    continue

        return deleted_files


monitoring_service = PilotMonitoringService()
