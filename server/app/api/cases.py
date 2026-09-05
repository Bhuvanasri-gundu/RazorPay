"""Recovery cases API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.supabase_service import get_supabase
from app.services.recovery_agent import (
    create_recovery_case, analyze_case, execute_recovery,
    approve_case, get_case_details
)
from app.models.schemas import FailedPaymentEvent
from app.services.audit_service import log_event

router = APIRouter(prefix="/api", tags=["Cases"])


@router.post("/events")
def ingest_failed_payment(event: FailedPaymentEvent):
    """Ingest a failed payment event and create a recovery case."""
    db = get_supabase()

    # Create the transaction
    txn = db.table("transactions").insert({
        "customer_id": event.customer_id,
        "amount": event.amount,
        "currency": event.currency,
        "payment_method": event.payment_method,
        "status": "FAILED",
        "failure_reason": event.failure_reason,
        "retry_count": 0,
    }).execute()

    txn_data = txn.data[0]

    # Create recovery case
    case = create_recovery_case(
        transaction_id=txn_data["id"],
        customer_id=event.customer_id,
        amount=event.amount,
    )

    return {"success": True, "case": case, "transaction": txn_data}


@router.get("/cases")
def list_cases(
    status: Optional[str] = None,
    failure_reason: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """List recovery cases with optional filtering, preserving live Supabase data alongside the mock dataset."""
    try:
        if hasattr(limit, "default"):
            limit = limit.default

        cases = []
        try:
            db = get_supabase()
            query = db.table("recovery_cases").select(
                "*, transactions!inner(amount, payment_method, failure_reason, status, retry_count), "
                "customers!inner(name, email, previous_success_rate)"
            )
            if status:
                query = query.eq("status", status)
            if action:
                query = query.eq("ai_recommendation", action)

            query = query.order("created_at", desc=True)
            result = query.execute()
            cases = result.data or []
        except Exception:
            cases = []

        # Merge mock recovery cases so both live Supabase cases and mock dataset are available
        try:
            from app.services.mock_database import get_mock_supabase
            mock_db = get_mock_supabase()
            mock_query = mock_db.table("recovery_cases").select(
                "*, transactions!inner(amount, payment_method, failure_reason, status, retry_count), "
                "customers!inner(name, email, previous_success_rate)"
            )
            if status:
                mock_query = mock_query.eq("status", status)
            if action:
                mock_query = mock_query.eq("ai_recommendation", action)
            mock_result = mock_query.execute()
            mock_cases = mock_result.data or []

            real_ids = {c["id"] for c in cases}
            for mc in mock_cases:
                if mc["id"] not in real_ids:
                    cases.append(mc)
        except Exception:
            pass

        # Filter by failure_reason at application level (it's in the joined table)
        if failure_reason:
            cases = [c for c in cases if c.get("transactions", {}).get("failure_reason") == failure_reason]

        total_count = len(cases)
        paged_cases = cases[offset : offset + limit]

        return {"cases": paged_cases, "count": total_count}
    except Exception as e:
        return {"cases": [], "count": 0}


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    """Get detailed case information."""
    try:
        details = get_case_details(case_id)
        return details
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Case not found: {str(e)}")


@router.post("/cases/{case_id}/analyze")
def analyze(case_id: str):
    """Run Gemini AI analysis on a recovery case."""
    try:
        result = analyze_case(case_id)
        return result
    except Exception as e:
        log_event(case_id, "Recovery Agent", "ERROR", f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cases/{case_id}/execute")
def execute(case_id: str):
    """Execute recovery action (after policy validation)."""
    try:
        result = execute_recovery(case_id)
        return result
    except Exception as e:
        log_event(case_id, "Recovery Agent", "ERROR", f"Execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cases/{case_id}/approve")
def approve(case_id: str):
    """Human approval for high-value cases."""
    try:
        result = approve_case(case_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
