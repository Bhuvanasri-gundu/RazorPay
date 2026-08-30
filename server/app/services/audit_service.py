"""Audit logging service — records every step of the recovery workflow."""

from app.services.supabase_service import get_supabase
from typing import Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

# In-memory buffer for audit logs if database is temporarily unavailable
_local_audit_buffer: list[dict] = []


def log_event(
    recovery_case_id: Optional[str],
    component: str,
    event_type: str,
    message: str,
    metadata: Optional[dict] = None,
) -> dict:
    """Insert an audit log entry into Supabase, with graceful in-memory fallback."""
    row = {
        "recovery_case_id": recovery_case_id,
        "component": component,
        "event_type": event_type,
        "message": message,
        "metadata": metadata or {},
        "created_at": datetime.utcnow().isoformat(),
    }
    try:
        db = get_supabase()
        result = db.table("audit_logs").insert({
            "recovery_case_id": row["recovery_case_id"],
            "component": row["component"],
            "event_type": row["event_type"],
            "message": row["message"],
            "metadata": row["metadata"],
        }).execute()
        return result.data[0] if result.data else row
    except Exception as e:
        logger.warning(f"[AuditLog Fallback] Could not persist audit log to Supabase: {e}")
        _local_audit_buffer.append(row)
        return row


def get_case_audit_trail(case_id: str) -> list[dict]:
    """Get all audit logs for a recovery case, chronologically."""
    try:
        db = get_supabase()
        result = (
            db.table("audit_logs")
            .select("*")
            .eq("recovery_case_id", case_id)
            .order("created_at", desc=False)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning(f"Could not retrieve audit logs from Supabase: {e}")
        return [r for r in _local_audit_buffer if r.get("recovery_case_id") == case_id]


# Convenient alias
get_audit_trail = get_case_audit_trail
