"""REVA Recovery Agent — orchestrates the full recovery workflow."""

import random
from app.services.supabase_service import get_supabase
from app.services.gemini_service import analyze_payment
from app.services.audit_service import log_event, get_case_audit_trail
from app.services.policy_engine import evaluate as evaluate_policy
from app.services.razorpay_service import create_payment_link
from app.models.schemas import RecoveryStatus, PolicyStatus


def create_recovery_case(transaction_id: str, customer_id: str, amount: float) -> dict:
    """Step 1: Create a recovery case for a failed transaction."""
    db = get_supabase()
    case = db.table("recovery_cases").insert({
        "transaction_id": transaction_id,
        "customer_id": customer_id,
        "amount_at_risk": amount,
        "status": RecoveryStatus.OPEN,
    }).execute()

    case_data = case.data[0]
    log_event(case_data["id"], "Revenue Loss Detector", "CASE_CREATED",
              f"Failed payment detected. Recovery case created. Amount at risk: INR {amount:,.2f}",
              {"transaction_id": transaction_id, "amount": amount})
    return case_data


def analyze_case(case_id: str) -> dict:
    """Step 2: Use Gemini AI to analyze the failure and recommend recovery action."""
    db = get_supabase()

    # Fetch case with transaction and customer data
    case = db.table("recovery_cases").select("*").eq("id", case_id).single().execute()
    case_data = case.data

    txn = db.table("transactions").select("*").eq("id", case_data["transaction_id"]).single().execute()
    txn_data = txn.data

    customer = db.table("customers").select("*").eq("id", case_data["customer_id"]).single().execute()
    cust_data = customer.data

    # Count previous failures for this customer
    prev_failures = db.table("transactions").select("id", count="exact").eq(
        "customer_id", case_data["customer_id"]).eq("status", "FAILED").execute()
    failure_count = prev_failures.count or 0

    # Count previous recovery attempts
    prev_recoveries = db.table("recovery_cases").select("id", count="exact").eq(
        "customer_id", case_data["customer_id"]).execute()
    recovery_count = prev_recoveries.count or 0

    # Update status to ANALYZING
    db.table("recovery_cases").update({"status": RecoveryStatus.ANALYZING}).eq("id", case_id).execute()
    log_event(case_id, "Recovery Agent", "ANALYSIS_STARTED", "AI analysis initiated.")

    # Call Gemini AI
    analysis = analyze_payment(
        case_id=case_id,
        amount=txn_data["amount"],
        payment_method=txn_data["payment_method"],
        failure_reason=txn_data.get("failure_reason", "UNKNOWN"),
        retry_count=txn_data.get("retry_count", 0),
        customer_success_rate=cust_data.get("previous_success_rate", 0.5),
        previous_failures=failure_count,
        recovery_attempts=recovery_count,
    )

    # Update case with AI results
    db.table("recovery_cases").update({
        "diagnosis": analysis.diagnosis,
        "ai_recommendation": analysis.recommended_action,
        "status": RecoveryStatus.ACTION_PENDING,
    }).eq("id", case_id).execute()

    log_event(case_id, "Gemini AI", "RECOMMENDATION",
              f"Recommended action: {analysis.recommended_action}. Reason: {analysis.reason}",
              {"diagnosis": analysis.diagnosis, "confidence": analysis.confidence,
               "customer_message": analysis.customer_message})

    return {
        "case_id": case_id,
        "diagnosis": analysis.diagnosis,
        "confidence": analysis.confidence,
        "recommended_action": analysis.recommended_action,
        "reason": analysis.reason,
        "customer_message": analysis.customer_message,
    }


def execute_recovery(case_id: str) -> dict:
    """Step 3: Validate through Policy Engine and execute the recovery action."""
    db = get_supabase()

    # Fetch case
    case = db.table("recovery_cases").select("*").eq("id", case_id).single().execute()
    case_data = case.data

    txn = db.table("transactions").select("*").eq("id", case_data["transaction_id"]).single().execute()
    txn_data = txn.data

    customer = db.table("customers").select("*").eq("id", case_data["customer_id"]).single().execute()
    cust_data = customer.data

    recommended_action = case_data.get("ai_recommendation", "ESCALATE")

    # Count contact attempts
    contact_actions = db.table("recovery_actions").select("id", count="exact").eq(
        "recovery_case_id", case_id).in_(
        "action_type", ["CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD"]).execute()
    contact_attempts = contact_actions.count or 0

    # --- POLICY ENGINE ---
    policy_decision = evaluate_policy(
        case_id=case_id,
        recommended_action=recommended_action,
        retry_count=txn_data.get("retry_count", 0),
        amount=txn_data["amount"],
        contact_attempts=contact_attempts,
    )

    # Handle policy decisions
    policy_dict = policy_decision.model_dump() if hasattr(policy_decision, "model_dump") else policy_decision.dict()

    if policy_decision.status == PolicyStatus.BLOCKED:
        db.table("recovery_cases").update({
            "status": RecoveryStatus.STOPPED_BY_POLICY,
            "selected_action": "BLOCKED",
        }).eq("id", case_id).execute()
        return {"case_id": case_id, "status": "STOPPED_BY_POLICY", "policy": policy_dict}

    if policy_decision.status == PolicyStatus.STOPPED_BY_POLICY:
        db.table("recovery_cases").update({
            "status": RecoveryStatus.STOPPED_BY_POLICY,
            "selected_action": recommended_action,
        }).eq("id", case_id).execute()
        return {"case_id": case_id, "status": "STOPPED_BY_POLICY", "policy": policy_dict}

    if policy_decision.status == PolicyStatus.REQUIRES_HUMAN_APPROVAL:
        db.table("recovery_cases").update({
            "status": RecoveryStatus.REQUIRES_HUMAN_APPROVAL,
            "selected_action": recommended_action,
        }).eq("id", case_id).execute()
        return {"case_id": case_id, "status": "REQUIRES_HUMAN_APPROVAL", "policy": policy_dict}

    # --- EXECUTE APPROVED ACTION ---
    db.table("recovery_cases").update({
        "status": RecoveryStatus.IN_PROGRESS,
        "selected_action": recommended_action,
    }).eq("id", case_id).execute()

    if recommended_action == "RETRY_LATER":
        return _execute_retry(case_id, case_data, txn_data, cust_data)

    elif recommended_action == "CREATE_PAYMENT_LINK":
        return _execute_payment_link(case_id, case_data, txn_data, cust_data)

    elif recommended_action == "RECOMMEND_ALTERNATIVE_METHOD":
        return _execute_alternative_method(case_id, case_data, txn_data, cust_data)

    elif recommended_action == "STOP_RECOVERY":
        return _execute_stop(case_id, case_data)

    elif recommended_action == "ESCALATE":
        return _execute_escalate(case_id, case_data)

    else:
        log_event(case_id, "Recovery Agent", "UNKNOWN_ACTION",
                  f"Unknown action: {recommended_action}")
        return {"case_id": case_id, "status": "ERROR", "message": f"Unknown action: {recommended_action}"}


def _execute_retry(case_id: str, case_data: dict, txn_data: dict, cust_data: dict) -> dict:
    """Simulate a retry attempt using deterministic logic."""
    db = get_supabase()

    log_event(case_id, "Recovery Executor", "RETRY_INITIATED",
              f"Simulating retry attempt (retry #{txn_data.get('retry_count', 0) + 1})")

    # Record recovery action
    db.table("recovery_actions").insert({
        "recovery_case_id": case_id,
        "action_type": "RETRY_LATER",
        "execution_status": "EXECUTING",
        "details": {"retry_count": txn_data.get("retry_count", 0) + 1},
    }).execute()

    # Deterministic simulation based on failure reason and customer history
    success_rate = cust_data.get("previous_success_rate", 0.5)
    failure_reason = txn_data.get("failure_reason", "")

    # Higher success for temporary failures
    if failure_reason in ("BANK_TIMEOUT", "TECHNICAL_FAILURE"):
        recovery_chance = 0.7 + (success_rate * 0.2)
    elif failure_reason == "UPI_TIMEOUT":
        recovery_chance = 0.4 + (success_rate * 0.2)
    elif failure_reason == "CARD_DECLINED":
        recovery_chance = 0.2 + (success_rate * 0.1)
    else:
        recovery_chance = 0.3

    # Lower chance with more retries
    recovery_chance -= txn_data.get("retry_count", 0) * 0.15
    recovery_chance = max(0.05, min(0.95, recovery_chance))

    # Ensure temporary bank timeouts with good customer history reliably recover on first retry
    if failure_reason in ("BANK_TIMEOUT", "TECHNICAL_FAILURE") and txn_data.get("retry_count", 0) <= 1 and success_rate >= 0.7:
        recovered = True
    else:
        # Stable deterministic seed based on case_id (independent of Python process salt)
        seed = sum(ord(c) for c in str(case_id)) % 10000
        rng = random.Random(seed)
        recovered = rng.random() < recovery_chance

    # Update retry count on transaction
    new_retry = txn_data.get("retry_count", 0) + 1
    db.table("transactions").update({"retry_count": new_retry}).eq("id", txn_data["id"]).execute()

    if recovered:
        amount = case_data["amount_at_risk"]
        db.table("recovery_cases").update({
            "status": RecoveryStatus.RECOVERED,
            "recovered_amount": amount,
        }).eq("id", case_id).execute()
        db.table("recovery_actions").update({
            "execution_status": "COMPLETED",
        }).eq("recovery_case_id", case_id).eq("action_type", "RETRY_LATER").execute()
        db.table("transactions").update({"status": "SUCCESS"}).eq("id", txn_data["id"]).execute()

        log_event(case_id, "Recovery Executor", "PAYMENT_RECOVERED",
                  f"Payment recovered! INR {amount:,.2f} recovered via retry.",
                  {"recovered_amount": amount})
        return {"case_id": case_id, "status": "RECOVERED", "recovered_amount": amount}
    else:
        db.table("recovery_cases").update({
            "status": RecoveryStatus.RECOVERY_FAILED,
        }).eq("id", case_id).execute()
        db.table("recovery_actions").update({
            "execution_status": "FAILED",
        }).eq("recovery_case_id", case_id).eq("action_type", "RETRY_LATER").execute()

        log_event(case_id, "Recovery Executor", "RETRY_FAILED",
                  "Retry attempt failed. Payment not recovered.")
        return {"case_id": case_id, "status": "RECOVERY_FAILED"}


def _execute_payment_link(case_id: str, case_data: dict, txn_data: dict, cust_data: dict) -> dict:
    """Create a Razorpay payment link for recovery."""
    db = get_supabase()

    log_event(case_id, "Recovery Executor", "PAYMENT_LINK_INITIATED",
              "Creating Razorpay payment link for recovery.")

    result = create_payment_link(
        case_id=case_id,
        amount=case_data["amount_at_risk"],
        customer_name=cust_data.get("name", "Customer"),
        customer_email=cust_data.get("email", ""),
        description=f"Payment Recovery - INR {case_data['amount_at_risk']:,.2f}",
    )

    action_data = {
        "recovery_case_id": case_id,
        "action_type": "CREATE_PAYMENT_LINK",
        "execution_status": "COMPLETED" if result.get("success") else "FAILED",
        "razorpay_payment_link_id": result.get("payment_link_id"),
        "details": result,
    }
    db.table("recovery_actions").insert(action_data).execute()

    if result.get("success"):
        db.table("recovery_cases").update({
            "status": RecoveryStatus.IN_PROGRESS,
        }).eq("id", case_id).execute()
        return {
            "case_id": case_id,
            "status": "PAYMENT_LINK_CREATED",
            "payment_link_url": result.get("short_url"),
            "payment_link_id": result.get("payment_link_id"),
        }
    else:
        db.table("recovery_cases").update({
            "status": RecoveryStatus.ESCALATED,
        }).eq("id", case_id).execute()
        log_event(case_id, "Recovery Executor", "ESCALATED",
                  f"Payment link creation failed: {result.get('error')}. Case escalated to manual review.")
        return {"case_id": case_id, "status": "ESCALATED", "error": result.get("error")}


def _execute_alternative_method(case_id: str, case_data: dict, txn_data: dict, cust_data: dict) -> dict:
    """Recommend an alternative payment method, optionally with a payment link."""
    db = get_supabase()

    method = txn_data.get("payment_method", "UPI")
    alternatives = {"UPI": "Card or Netbanking", "CARD": "UPI or Netbanking",
                    "NETBANKING": "UPI or Card", "WALLET": "UPI, Card, or Netbanking"}
    alt_text = alternatives.get(method, "another payment method")

    message = f"Your {method} payment of INR {case_data['amount_at_risk']:,.2f} failed. Please try using {alt_text}."

    log_event(case_id, "Recovery Executor", "ALTERNATIVE_RECOMMENDED",
              f"Recommended alternative: {alt_text}",
              {"original_method": method, "customer_message": message})

    # Also try to create a payment link
    result = create_payment_link(
        case_id=case_id,
        amount=case_data["amount_at_risk"],
        customer_name=cust_data.get("name", "Customer"),
        customer_email=cust_data.get("email", ""),
        description=f"Payment Recovery - Try {alt_text}",
    )

    action_data = {
        "recovery_case_id": case_id,
        "action_type": "RECOMMEND_ALTERNATIVE_METHOD",
        "execution_status": "COMPLETED",
        "razorpay_payment_link_id": result.get("payment_link_id") if result.get("success") else None,
        "details": {"message": message, "alternative": alt_text, "payment_link": result},
    }
    db.table("recovery_actions").insert(action_data).execute()

    db.table("recovery_cases").update({
        "status": RecoveryStatus.IN_PROGRESS,
    }).eq("id", case_id).execute()

    return {
        "case_id": case_id,
        "status": "ALTERNATIVE_RECOMMENDED",
        "message": message,
        "payment_link_url": result.get("short_url") if result.get("success") else None,
    }


def _execute_stop(case_id: str, case_data: dict) -> dict:
    """Stop recovery — no further action."""
    db = get_supabase()

    db.table("recovery_actions").insert({
        "recovery_case_id": case_id,
        "action_type": "STOP_RECOVERY",
        "execution_status": "COMPLETED",
        "details": {"reason": "AI and Policy agreed to stop recovery."},
    }).execute()

    db.table("recovery_cases").update({
        "status": RecoveryStatus.STOPPED,
    }).eq("id", case_id).execute()

    log_event(case_id, "Recovery Executor", "RECOVERY_STOPPED",
              "Recovery stopped. No further action will be taken.")

    return {"case_id": case_id, "status": "STOPPED"}


def _execute_escalate(case_id: str, case_data: dict) -> dict:
    """Escalate to manual review."""
    db = get_supabase()

    db.table("recovery_actions").insert({
        "recovery_case_id": case_id,
        "action_type": "ESCALATE",
        "execution_status": "COMPLETED",
        "details": {"reason": "Case escalated for manual review."},
    }).execute()

    db.table("recovery_cases").update({
        "status": RecoveryStatus.ESCALATED,
    }).eq("id", case_id).execute()

    log_event(case_id, "Recovery Executor", "ESCALATED",
              "Case escalated to manual review.")

    return {"case_id": case_id, "status": "ESCALATED"}


def approve_case(case_id: str) -> dict:
    """Human approval for high-value cases."""
    db = get_supabase()

    case = db.table("recovery_cases").select("*").eq("id", case_id).single().execute()
    case_data = case.data

    if case_data["status"] != RecoveryStatus.REQUIRES_HUMAN_APPROVAL:
        return {"case_id": case_id, "error": "Case does not require approval."}

    log_event(case_id, "Human Operator", "APPROVED",
              "High-value case approved by human operator.")

    # Re-run execution with approval bypass — temporarily lower the amount for policy
    # Actually, just set the status and re-execute
    db.table("recovery_cases").update({
        "status": RecoveryStatus.ACTION_PENDING,
    }).eq("id", case_id).execute()

    # For approved high-value cases, execute directly
    txn = db.table("transactions").select("*").eq("id", case_data["transaction_id"]).single().execute()
    cust = db.table("customers").select("*").eq("id", case_data["customer_id"]).single().execute()

    recommended = case_data.get("ai_recommendation", "ESCALATE")

    db.table("recovery_cases").update({
        "status": RecoveryStatus.IN_PROGRESS,
        "selected_action": recommended,
    }).eq("id", case_id).execute()

    log_event(case_id, "Policy Engine", "HUMAN_OVERRIDE",
              f"Human approved. Executing action: {recommended}")

    if recommended == "RETRY_LATER":
        return _execute_retry(case_id, case_data, txn.data, cust.data)
    elif recommended == "CREATE_PAYMENT_LINK":
        return _execute_payment_link(case_id, case_data, txn.data, cust.data)
    elif recommended == "RECOMMEND_ALTERNATIVE_METHOD":
        return _execute_alternative_method(case_id, case_data, txn.data, cust.data)
    else:
        return _execute_escalate(case_id, case_data)


def get_case_details(case_id: str) -> dict:
    """Get full case details including transaction, customer, actions, and audit trail."""
    db = get_supabase()

    case = db.table("recovery_cases").select("*").eq("id", case_id).single().execute()
    case_data = case.data

    txn = db.table("transactions").select("*").eq("id", case_data["transaction_id"]).single().execute()
    cust = db.table("customers").select("*").eq("id", case_data["customer_id"]).single().execute()
    actions = db.table("recovery_actions").select("*").eq("recovery_case_id", case_id).order("created_at").execute()
    audit = get_case_audit_trail(case_id)

    return {
        "case": case_data,
        "transaction": txn.data,
        "customer": cust.data,
        "actions": actions.data or [],
        "audit_trail": audit,
    }


# Convenient alias
approve_action = approve_case
