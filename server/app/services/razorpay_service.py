"""Razorpay integration service — payment link creation and verification with mock mode support."""

import uuid
import traceback
import logging
import concurrent.futures
from app.config import get_settings
from app.services.audit_service import log_event

logger = logging.getLogger(__name__)


def _get_client():
    settings = get_settings()
    if not settings.is_razorpay_active:
        return None
    import razorpay
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


def create_payment_link(
    case_id: str,
    amount: float,
    customer_name: str,
    customer_email: str,
    description: str = "Payment Recovery - REVA",
) -> dict:
    """Create a Razorpay payment link in test mode, or graceful mock link if unconfigured."""
    settings = get_settings()

    # REAL RAZORPAY TEST MODE
    if settings.is_razorpay_active:
        try:
            client = _get_client()
            amount_paise = int(amount * 100)

            payload = {
                "amount": amount_paise,
                "currency": "INR",
                "description": description,
                "customer": {
                    "name": customer_name,
                    "email": customer_email,
                },
                "notify": {
                    "email": False,
                    "sms": False,
                },
                "callback_url": "",
                "callback_method": "get",
                "notes": {
                    "recovery_case_id": case_id,
                    "source": "REVA",
                },
            }

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(client.payment_link.create, payload)
                result = future.result(timeout=2.0)

            log_event(case_id, "Razorpay", "PAYMENT_LINK_CREATED",
                      f"Razorpay payment link created: {result.get('short_url', 'N/A')}",
                      {"payment_link_id": result.get("id"), "amount": amount, "mode": "real_test"})

            return {
                "success": True,
                "payment_link_id": result.get("id"),
                "short_url": result.get("short_url"),
                "amount": amount,
                "status": result.get("status"),
                "is_mock": False,
            }
        except Exception as e:
            log_event(case_id, "Razorpay", "API_ERROR",
                      f"Razorpay API error ({str(e)}). Using simulated link.",
                      {"traceback": traceback.format_exc()})
            # Fallback to simulated link on API error
            return _generate_mock_link(case_id, amount, description)

    # MOCK MODE
    return _generate_mock_link(case_id, amount, description)


def _generate_mock_link(case_id: str, amount: float, description: str) -> dict:
    """Generate clearly labeled simulated test payment link."""
    link_id = f"plink_mock_{uuid.uuid4().hex[:12]}"
    short_url = f"https://rzp.io/i/mock_reva_{uuid.uuid4().hex[:8]}"

    log_event(
        case_id,
        "Razorpay",
        "MOCK_LINK_CREATED",
        f"[Mock Mode] Simulated payment link generated: {short_url}",
        {"payment_link_id": link_id, "amount": amount, "is_mock": True},
    )

    return {
        "success": True,
        "payment_link_id": link_id,
        "short_url": short_url,
        "amount": amount,
        "status": "created",
        "is_mock": True,
        "note": "Simulated link (add RAZORPAY_KEY_ID & RAZORPAY_KEY_SECRET to use live test API)",
    }


def verify_payment(
    case_id: str,
    payment_link_id: str,
) -> dict:
    """Check the status of a Razorpay payment link."""
    settings = get_settings()

    if settings.is_razorpay_active and not payment_link_id.startswith("plink_mock_"):
        try:
            client = _get_client()
            result = client.payment_link.fetch(payment_link_id)

            status = result.get("status", "unknown")
            amount_paid = result.get("amount_paid", 0) / 100

            log_event(case_id, "Razorpay", "PAYMENT_VERIFIED",
                      f"Razorpay payment link status: {status}, amount paid: INR {amount_paid:,.2f}",
                      {"payment_link_id": payment_link_id, "status": status, "is_mock": False})

            return {
                "success": True,
                "status": status,
                "amount_paid": amount_paid,
                "payment_link_id": payment_link_id,
                "is_mock": False,
            }
        except Exception as e:
            log_event(case_id, "Razorpay", "VERIFY_ERROR",
                      f"Razorpay verification failed: {str(e)}",
                      {"traceback": traceback.format_exc()})
            return {"success": False, "error": str(e)}

    # Mock mode verification
    log_event(case_id, "Razorpay", "MOCK_PAYMENT_VERIFIED",
              f"[Mock Mode] Simulated payment verification for {payment_link_id} marked as PAID.",
              {"payment_link_id": payment_link_id, "status": "paid", "is_mock": True})

    return {
        "success": True,
        "status": "paid",
        "amount_paid": 0,
        "payment_link_id": payment_link_id,
        "is_mock": True,
    }
