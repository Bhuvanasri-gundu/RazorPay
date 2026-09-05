"""Dashboard and analytics API endpoints."""

import logging
from fastapi import APIRouter
from app.services.supabase_service import get_supabase
from app.models.schemas import DashboardMetrics, AnalyticsData

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics():
    """Get top-level dashboard metrics with graceful fallback if DB is not configured."""
    try:
        db = get_supabase()

        # Real Supabase cases
        cases = db.table("recovery_cases").select("id, amount_at_risk, recovered_amount, status").execute()
        case_list = list(cases.data or [])

        # Total transactions from Supabase
        txns = db.table("transactions").select("id, amount, status", count="exact").execute()
        total_txns = txns.count or len(txns.data or [])
        failed_txns = [t for t in (txns.data or []) if t["status"] == "FAILED"]
        total_failed = len(failed_txns)

        # Merge with mock data so full dataset is available alongside live Supabase records
        try:
            from app.services.mock_database import get_mock_supabase
            mock_db = get_mock_supabase()
            mock_cases = mock_db.table("recovery_cases").select("id, amount_at_risk, recovered_amount, status").execute()
            real_ids = {c["id"] for c in case_list}
            for mc in (mock_cases.data or []):
                if mc["id"] not in real_ids:
                    case_list.append(mc)

            mock_txns = mock_db.table("transactions").select("id, amount, status", count="exact").execute()
            total_txns += (mock_txns.count or len(mock_txns.data or []))
            mock_failed = [t for t in (mock_txns.data or []) if t["status"] == "FAILED"]
            total_failed += len(mock_failed)
        except Exception:
            pass

        total_risk = sum(c["amount_at_risk"] for c in case_list)
        total_recovered = sum(c.get("recovered_amount", 0) or 0 for c in case_list)

        active_statuses = {"OPEN", "ANALYZING", "ACTION_PENDING", "IN_PROGRESS"}
        active = sum(1 for c in case_list if c["status"] in active_statuses)
        stopped = sum(1 for c in case_list if c["status"] == "STOPPED_BY_POLICY")

        recovery_rate = (total_recovered / total_risk * 100) if total_risk > 0 else 0

        return DashboardMetrics(
            total_revenue_at_risk=total_risk,
            total_revenue_recovered=total_recovered,
            recovery_rate=round(recovery_rate, 1),
            active_recovery_cases=active,
            cases_stopped_by_policy=stopped,
            total_cases=len(case_list),
            total_transactions=total_txns,
            total_failed=total_failed,
        )
    except Exception as e:
        logger.warning(f"Could not fetch dashboard metrics from database: {e}")
        return DashboardMetrics(
            total_revenue_at_risk=0.0,
            total_revenue_recovered=0.0,
            recovery_rate=0.0,
            active_recovery_cases=0,
            cases_stopped_by_policy=0,
            total_cases=0,
            total_transactions=0,
            total_failed=0,
        )


@router.get("/analytics")
def get_analytics():
    """Get chart data for the dashboard with graceful fallback."""
    try:
        db = get_supabase()

        cases = db.table("recovery_cases").select("*").execute()
        case_list = list(cases.data or [])

        # Merge with mock data
        from app.services.mock_database import get_mock_supabase
        mock_db = get_mock_supabase()
        try:
            mock_cases = mock_db.table("recovery_cases").select("*").execute()
            real_ids = {c["id"] for c in case_list}
            for mc in (mock_cases.data or []):
                if mc["id"] not in real_ids:
                    case_list.append(mc)
        except Exception:
            pass

        # Cases by status
        status_counts: dict[str, int] = {}
        for c in case_list:
            s = c["status"]
            status_counts[s] = status_counts.get(s, 0) + 1
        cases_by_status = [{"status": k, "count": v} for k, v in status_counts.items()]

        # Failure reason distribution
        txn_ids = [c["transaction_id"] for c in case_list]
        failure_counts: dict[str, int] = {}
        if txn_ids:
            try:
                txns = db.table("transactions").select("failure_reason").in_("id", txn_ids[:100]).execute()
                for t in (txns.data or []):
                    r = t.get("failure_reason") or "UNKNOWN"
                    failure_counts[r] = failure_counts.get(r, 0) + 1
            except Exception:
                pass
            try:
                mock_txns = mock_db.table("transactions").select("id, failure_reason").execute()
                for t in (mock_txns.data or []):
                    if t["id"] in set(txn_ids):
                        r = t.get("failure_reason") or "UNKNOWN"
                        failure_counts[r] = failure_counts.get(r, 0) + 1
            except Exception:
                pass
        failure_distribution = [{"reason": k, "count": v} for k, v in failure_counts.items()]

        # Recovery action distribution
        action_counts: dict[str, int] = {}
        try:
            actions = db.table("recovery_actions").select("action_type").execute()
            for a in (actions.data or []):
                at = a["action_type"]
                action_counts[at] = action_counts.get(at, 0) + 1
        except Exception:
            pass
        try:
            mock_actions = mock_db.table("recovery_actions").select("action_type").execute()
            for a in (mock_actions.data or []):
                at = a["action_type"]
                action_counts[at] = action_counts.get(at, 0) + 1
        except Exception:
            pass
        action_distribution = [{"action": k, "count": v} for k, v in action_counts.items()]

        # Recovery timeline
        timeline: dict[str, dict] = {}
        for c in case_list:
            date = (c.get("created_at") or "")[:10]
            if date:
                if date not in timeline:
                    timeline[date] = {"date": date, "at_risk": 0, "recovered": 0}
                timeline[date]["at_risk"] += c.get("amount_at_risk", 0)
                timeline[date]["recovered"] += c.get("recovered_amount", 0) or 0

        recovery_timeline = sorted(timeline.values(), key=lambda x: x["date"])

        return {
            "cases_by_status": cases_by_status,
            "failure_reason_distribution": failure_distribution,
            "recovery_action_distribution": action_distribution,
            "recovery_timeline": recovery_timeline,
        }
    except Exception as e:
        logger.warning(f"Could not fetch dashboard analytics from database: {e}")
        return {
            "cases_by_status": [],
            "failure_reason_distribution": [],
            "recovery_action_distribution": [],
            "recovery_timeline": [],
        }
