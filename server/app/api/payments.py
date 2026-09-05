"""Payments API endpoints — Razorpay integration."""

from fastapi import APIRouter, HTTPException
from app.models.schemas import PaymentLinkRequest, PaymentVerifyRequest, RecoveryStatus
from app.services.razorpay_service import create_payment_link, verify_payment
from app.services.supabase_service import get_supabase
from app.services.audit_service import log_event

router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.post("/create-link")
def create_link(req: PaymentLinkRequest):
    """Create a Razorpay payment link for recovery."""
    result = create_payment_link(
        case_id=req.recovery_case_id,
        amount=req.amount,
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        description=req.description,
    )

    if result.get("success"):
        # Store payment link in recovery actions
        db = get_supabase()
        db.table("recovery_actions").insert({
            "recovery_case_id": req.recovery_case_id,
            "action_type": "CREATE_PAYMENT_LINK",
            "execution_status": "COMPLETED",
            "razorpay_payment_link_id": result.get("payment_link_id"),
            "details": result,
        }).execute()

    return result


@router.post("/verify")
def verify(req: PaymentVerifyRequest):
    """Verify payment status and update recovery case."""
    result = verify_payment(req.recovery_case_id, req.razorpay_payment_link_id)

    if result.get("success") and result.get("status") == "paid":
        db = get_supabase()
        amount_paid = result.get("amount_paid", 0)

        # Retrieve case to get amount_at_risk if amount_paid is zero/mock
        if not amount_paid or amount_paid <= 0:
            case_row = db.table("recovery_cases").select("amount_at_risk, transaction_id").eq("id", req.recovery_case_id).single().execute()
            if case_row.data:
                amount_paid = case_row.data.get("amount_at_risk", 0)
                txn_id = case_row.data.get("transaction_id")
                if txn_id:
                    db.table("transactions").update({"status": "SUCCESS"}).eq("id", txn_id).execute()

        db.table("recovery_cases").update({
            "status": RecoveryStatus.RECOVERED,
            "recovered_amount": amount_paid,
        }).eq("id", req.recovery_case_id).execute()

        db.table("recovery_actions").update({
            "execution_status": "COMPLETED",
        }).eq("recovery_case_id", req.recovery_case_id).execute()

        log_event(req.recovery_case_id, "Recovery Executor", "PAYMENT_RECOVERED",
                  f"Payment verified and recovered! INR {amount_paid:,.2f}",
                  {"payment_link_id": req.razorpay_payment_link_id, "recovered_amount": amount_paid})

    return result
