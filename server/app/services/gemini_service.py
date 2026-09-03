"""Gemini AI service — analyzes failed payments and recommends recovery actions."""

import json
import traceback
import concurrent.futures
from google import genai
from app.config import get_settings
from app.models.schemas import GeminiAnalysis
from app.services.audit_service import log_event


SYSTEM_PROMPT = """You are REVA, an AI Revenue Recovery Agent for a payments company.
You analyze failed payment transactions and recommend the best recovery action.

You MUST respond with ONLY valid JSON in this exact format:
{
  "diagnosis": "brief diagnosis of why the payment failed",
  "confidence": "high" or "medium" or "low",
  "recommended_action": one of "RETRY_LATER", "CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD", "STOP_RECOVERY", "ESCALATE",
  "reason": "brief explainable reason for the recommendation",
  "customer_message": "short personalized message to send to the customer"
}

Rules:
- BANK_TIMEOUT or TECHNICAL_FAILURE with low retry count → usually RETRY_LATER
- UPI_TIMEOUT with multiple failures → RECOMMEND_ALTERNATIVE_METHOD
- CARD_DECLINED → depends on reason, often CREATE_PAYMENT_LINK or RECOMMEND_ALTERNATIVE_METHOD
- INSUFFICIENT_BALANCE → usually STOP_RECOVERY or CREATE_PAYMENT_LINK with delay
- High retry count (>=3) → STOP_RECOVERY or ESCALATE
- Low customer success rate (<30%) → consider STOP_RECOVERY
- High value (>50000) → be cautious, consider ESCALATE

Respond with ONLY the JSON object. No markdown, no explanation, no code fences."""


def build_user_prompt(
    amount: float,
    payment_method: str,
    failure_reason: str,
    retry_count: int,
    customer_success_rate: float,
    previous_failures: int = 0,
    recovery_attempts: int = 0,
) -> str:
    return f"""Analyze this failed payment:

Amount: ₹{amount:,.2f}
Payment Method: {payment_method}
Failure Reason: {failure_reason}
Retry Count: {retry_count}
Customer Success Rate: {customer_success_rate:.0%}
Previous Failures: {previous_failures}
Recovery Attempts: {recovery_attempts}

Respond with ONLY a JSON object."""


def analyze_payment(
    case_id: str,
    amount: float,
    payment_method: str,
    failure_reason: str,
    retry_count: int,
    customer_success_rate: float,
    previous_failures: int = 0,
    recovery_attempts: int = 0,
) -> GeminiAnalysis:
    """Call Gemini AI to analyze a failed payment. Returns validated GeminiAnalysis."""
    settings = get_settings()

    if not settings.is_gemini_active:
        log_event(case_id, "Gemini AI", "MOCK_ANALYSIS", "[Mock AI Mode] Gemini API key not configured. Using deterministic AI diagnosis.")
        return _fallback_analysis(failure_reason, retry_count, customer_success_rate)

    client = genai.Client(api_key=settings.gemini_api_key)
    user_prompt = build_user_prompt(
        amount, payment_method, failure_reason, retry_count,
        customer_success_rate, previous_failures, recovery_attempts
    )

    model_name = settings.gemini_model
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                client.models.generate_content,
                model=model_name,
                contents=f"{SYSTEM_PROMPT}\n\n{user_prompt}",
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )
            response = future.result(timeout=2.0)
        raw = response.text.strip()

        # Clean possible markdown fences if returned
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        parsed = json.loads(raw)

        # Robust confidence normalization
        conf = parsed.get("confidence", "high")
        if isinstance(conf, (int, float)):
            conf = "high" if conf >= 0.7 else ("medium" if conf >= 0.4 else "low")
        elif isinstance(conf, str):
            conf_str = conf.strip().lower()
            conf = "high" if "high" in conf_str else ("low" if "low" in conf_str else "medium")
        else:
            conf = "high"
        parsed["confidence"] = conf

        # Robust recommended_action normalization
        action = str(parsed.get("recommended_action", "")).strip().upper()
        valid_actions = {
            "RETRY_LATER",
            "CREATE_PAYMENT_LINK",
            "RECOMMEND_ALTERNATIVE_METHOD",
            "STOP_RECOVERY",
            "ESCALATE",
        }
        if action not in valid_actions:
            if "ALTERNATIVE" in action or "METHOD" in action:
                action = "RECOMMEND_ALTERNATIVE_METHOD"
            elif "LINK" in action:
                action = "CREATE_PAYMENT_LINK"
            elif "RETRY" in action:
                action = "RETRY_LATER"
            elif "STOP" in action:
                action = "STOP_RECOVERY"
            else:
                action = "RECOMMEND_ALTERNATIVE_METHOD"
        parsed["recommended_action"] = action

        analysis = GeminiAnalysis(**parsed)

        log_event(case_id, "Gemini AI", "ANALYSIS_COMPLETE",
                  f"Diagnosis: {analysis.diagnosis}",
                  {"confidence": analysis.confidence, "model": model_name, "raw_response": raw})
        return analysis

    except concurrent.futures.TimeoutError:
        log_event(case_id, "Gemini AI", "TIMEOUT",
                  f"Gemini API response timed out (>2.0s). Transitioned to deterministic AI heuristic engine.",
                  {"model": model_name, "fallback": True})
    except json.JSONDecodeError:
        log_event(case_id, "Gemini AI", "PARSE_ERROR",
                  f"Invalid response format received from {model_name}. Transitioned to deterministic AI heuristic engine.",
                  {"model": model_name, "fallback": True})
    except Exception as e:
        err_str = str(e)
        if any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "quota", "Quota", "rate limit"]):
            log_event(case_id, "Gemini AI", "QUOTA_EXHAUSTED",
                      f"Gemini API quota reached / rate limit active for {model_name}. Transitioned to deterministic AI heuristic engine.",
                      {"model": model_name, "error_code": 429, "fallback": True})
        elif any(k in err_str for k in ["API_KEY", "401", "403", "PERMISSION_DENIED"]):
            log_event(case_id, "Gemini AI", "AUTH_UNAVAILABLE",
                      f"Gemini API key authorization unavailable. Transitioned to deterministic AI heuristic engine.",
                      {"model": model_name, "fallback": True})
        else:
            log_event(case_id, "Gemini AI", "API_UNAVAILABLE",
                      f"Gemini API temporarily unavailable ({model_name}). Transitioned to deterministic AI heuristic engine.",
                      {"model": model_name, "fallback": True})

    # Graceful deterministic fallback
    fallback_res = _fallback_analysis(failure_reason, retry_count, customer_success_rate)
    log_event(case_id, "Gemini AI", "FALLBACK_ACTIVATED",
              f"AI Diagnosis (Heuristic Fallback): {fallback_res.diagnosis}",
              {"recommended_action": fallback_res.recommended_action, "confidence": fallback_res.confidence, "mode": "heuristic_fallback"})
    return fallback_res


def _fallback_analysis(failure_reason: str, retry_count: int, success_rate: float) -> GeminiAnalysis:
    """Deterministic fallback when Gemini is unavailable or returns bad data."""
    if retry_count >= 3:
        return GeminiAnalysis(
            diagnosis=f"Multiple retries exhausted for {failure_reason}",
            confidence="high",
            recommended_action="STOP_RECOVERY",
            reason="Maximum retry limit reached",
            customer_message=None,
        )

    if success_rate < 0.3:
        return GeminiAnalysis(
            diagnosis=f"Low customer success rate with {failure_reason}",
            confidence="medium",
            recommended_action="STOP_RECOVERY",
            reason="Customer has very low payment success history",
            customer_message=None,
        )

    if failure_reason in ("BANK_TIMEOUT", "TECHNICAL_FAILURE"):
        return GeminiAnalysis(
            diagnosis=f"Temporary failure: {failure_reason}",
            confidence="medium",
            recommended_action="RETRY_LATER",
            reason="Failure appears temporary, retry is safe",
            customer_message="Your payment failed due to a temporary issue. We will retry shortly.",
        )

    if failure_reason == "UPI_TIMEOUT":
        return GeminiAnalysis(
            diagnosis="UPI service timeout",
            confidence="medium",
            recommended_action="RECOMMEND_ALTERNATIVE_METHOD",
            reason="UPI appears unreliable, suggest alternative",
            customer_message="UPI payment failed. Please try Card or Netbanking.",
        )

    if failure_reason == "CARD_DECLINED":
        return GeminiAnalysis(
            diagnosis="Card was declined by issuing bank",
            confidence="medium",
            recommended_action="CREATE_PAYMENT_LINK",
            reason="Card declined — send payment link for alternative method",
            customer_message="Your card payment was declined. Please use this payment link to complete your purchase.",
        )

    if failure_reason == "INSUFFICIENT_BALANCE":
        return GeminiAnalysis(
            diagnosis="Insufficient balance in customer account",
            confidence="high",
            recommended_action="STOP_RECOVERY",
            reason="Customer lacks sufficient funds — further retries may cause friction",
            customer_message=None,
        )

    return GeminiAnalysis(
        diagnosis=f"Payment failed: {failure_reason}",
        confidence="low",
        recommended_action="ESCALATE",
        reason="Unable to determine best recovery action",
        customer_message=None,
    )
