"""Deterministic Policy Engine — validates AI recommendations before execution."""

from app.models.schemas import PolicyDecision, PolicyStatus
from app.services.audit_service import log_event

# Policy constants
MAX_RETRIES = 3
MAX_CONTACT_ATTEMPTS = 2
HIGH_VALUE_THRESHOLD = 50000


def evaluate(
    case_id: str,
    recommended_action: str,
    retry_count: int,
    amount: float,
    contact_attempts: int = 0,
) -> PolicyDecision:
    """
    Evaluate an AI-recommended action against deterministic policy rules.
    Policy ALWAYS overrides AI recommendation.
    """

    # Rule 1: Max retries exceeded
    if recommended_action == "RETRY_LATER" and retry_count >= MAX_RETRIES:
        decision = PolicyDecision(
            status=PolicyStatus.STOPPED_BY_POLICY,
            reason=f"Retry count ({retry_count}) has reached maximum ({MAX_RETRIES}). No further retries allowed."
        )
        log_event(case_id, "Policy Engine", "BLOCKED",
                  decision.reason, {"rule": "MAX_RETRIES", "retry_count": retry_count})
        return decision

    # Rule 2: High value transaction
    if amount >= HIGH_VALUE_THRESHOLD:
        decision = PolicyDecision(
            status=PolicyStatus.REQUIRES_HUMAN_APPROVAL,
            reason=f"Transaction amount INR {amount:,.2f} exceeds high-value threshold (INR {HIGH_VALUE_THRESHOLD:,.2f}). Requires human approval."
        )
        log_event(case_id, "Policy Engine", "REQUIRES_APPROVAL",
                  decision.reason, {"rule": "HIGH_VALUE", "amount": amount})
        return decision

    # Rule 3: AI says stop
    if recommended_action == "STOP_RECOVERY":
        decision = PolicyDecision(
            status=PolicyStatus.APPROVED,
            reason="AI recommends stopping recovery. Policy confirms."
        )
        log_event(case_id, "Policy Engine", "APPROVED",
                  decision.reason, {"rule": "AI_STOP"})
        return decision

    # Rule 4: Max contact attempts
    if recommended_action in ("RECOMMEND_ALTERNATIVE_METHOD", "CREATE_PAYMENT_LINK"):
        if contact_attempts >= MAX_CONTACT_ATTEMPTS:
            decision = PolicyDecision(
                status=PolicyStatus.STOPPED_BY_POLICY,
                reason=f"Contact attempts ({contact_attempts}) reached maximum ({MAX_CONTACT_ATTEMPTS}). No further contact allowed."
            )
            log_event(case_id, "Policy Engine", "BLOCKED",
                      decision.reason, {"rule": "MAX_CONTACTS", "contact_attempts": contact_attempts})
            return decision

    # Rule 5: Valid action within limits
    valid_actions = {"RETRY_LATER", "CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD", "STOP_RECOVERY", "ESCALATE"}
    if recommended_action in valid_actions:
        decision = PolicyDecision(
            status=PolicyStatus.APPROVED,
            reason=f"Action '{recommended_action}' is within policy limits."
        )
        log_event(case_id, "Policy Engine", "APPROVED",
                  decision.reason, {"action": recommended_action})
        return decision

    # Rule 6: Unknown action
    decision = PolicyDecision(
        status=PolicyStatus.BLOCKED,
        reason=f"Unknown action '{recommended_action}' is not permitted by policy."
    )
    log_event(case_id, "Policy Engine", "BLOCKED",
              decision.reason, {"action": recommended_action})
    return decision
