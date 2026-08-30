"""REVA Services Layer — Gemini AI, Policy Engine, Recovery Agent, Razorpay, and Database."""

from app.services.gemini_service import analyze_payment, build_user_prompt
from app.services.policy_engine import evaluate as evaluate_policy
from app.services.razorpay_service import create_payment_link, verify_payment
from app.services.recovery_agent import create_recovery_case, analyze_case, execute_recovery, approve_action, get_case_details
from app.services.audit_service import log_event, get_audit_trail
from app.services.supabase_service import get_supabase
from app.services.mock_database import MockSupabaseClient, get_mock_supabase

__all__ = [
    "analyze_payment",
    "build_user_prompt",
    "evaluate_policy",
    "create_payment_link",
    "verify_payment",
    "create_recovery_case",
    "analyze_case",
    "execute_recovery",
    "approve_action",
    "get_case_details",
    "log_event",
    "get_audit_trail",
    "get_supabase",
    "MockSupabaseClient",
    "get_mock_supabase",
]
