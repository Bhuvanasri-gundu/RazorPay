"""Unit and integration test suite for REVA Core Engine.

Runs with standard library unittest: python -m unittest discover tests
"""

import unittest
from app.config import get_settings, Settings
from app.services.policy_engine import evaluate as evaluate_policy
from app.services.gemini_service import analyze_payment, _fallback_analysis
from app.services.razorpay_service import create_payment_link, verify_payment
from app.services.supabase_service import get_supabase
from app.api.dashboard import get_metrics, get_analytics
from app.api.demo import run_demo_scenario, run_custom_scenario
from app.models.schemas import DemoScenarioRequest, CustomScenarioRequest


class TestConfigurationModes(unittest.TestCase):
    """Test configuration auto-detection and safe fallback flags."""

    def test_placeholder_detection(self):
        # Placeholder keys should evaluate to False (active=False)
        s = Settings(
            gemini_api_key="YOUR_GEMINI_API_KEY_HERE",
            supabase_url="YOUR_SUPABASE_PROJECT_URL_HERE",
            supabase_service_role_key="YOUR_SUPABASE_SECRET_KEY_HERE",
            razorpay_key_id="YOUR_RAZORPAY_TEST_KEY_ID_HERE",
            razorpay_key_secret="YOUR_RAZORPAY_TEST_KEY_SECRET_HERE",
        )
        self.assertFalse(s.is_gemini_active)
        self.assertFalse(s.is_supabase_active)
        self.assertFalse(s.is_razorpay_active)

    def test_real_keys_detection(self):
        # Valid active keys should evaluate to True (active=True)
        s = Settings(
            gemini_api_key="TEST_VALID_ACTIVE_GEMINI_KEY_OVER_15_CHARS",
            supabase_url="https://validproject.supabase.co",
            supabase_service_role_key="TEST_VALID_SUPABASE_SERVICE_ROLE_KEY_OVER_20_CHARS",
            razorpay_key_id="rzp_test_simulated_active_key",
            razorpay_key_secret="secret_key_valid_12345",
        )
        self.assertTrue(s.is_gemini_active)
        self.assertTrue(s.is_supabase_active)
        self.assertTrue(s.is_razorpay_active)


class TestPolicyEngine(unittest.TestCase):
    """Test deterministic business rules and safety guardrails."""

    def test_high_value_rule_requires_human_approval(self):
        # Transactions >= 50,000 must require human approval
        decision = evaluate_policy("case_1", "RETRY_LATER", retry_count=0, amount=75000)
        self.assertEqual(decision.status, "REQUIRES_HUMAN_APPROVAL")
        self.assertIn("50,000", decision.reason)

    def test_max_retry_rule_stops_recovery(self):
        # Retry count >= 3 must be blocked by policy
        decision = evaluate_policy("case_2", "RETRY_LATER", retry_count=3, amount=2499)
        self.assertEqual(decision.status, "STOPPED_BY_POLICY")
        self.assertIn("maximum", decision.reason.lower())

    def test_normal_action_approved(self):
        # Within limits should be approved
        decision = evaluate_policy("case_3", "RETRY_LATER", retry_count=1, amount=2499)
        self.assertEqual(decision.status, "APPROVED")

    def test_stop_recovery_action_approved(self):
        # AI advising stop recovery is verified and approved
        decision = evaluate_policy("case_4", "STOP_RECOVERY", retry_count=1, amount=199)
        self.assertEqual(decision.status, "APPROVED")


class TestGeminiDiagnosis(unittest.TestCase):
    """Test AI diagnosis and deterministic fallback heuristics."""

    def test_fallback_bank_timeout(self):
        analysis = _fallback_analysis("BANK_TIMEOUT", retry_count=0, success_rate=0.85)
        self.assertEqual(analysis.recommended_action, "RETRY_LATER")
        self.assertIn("timeout", analysis.diagnosis.lower())

    def test_fallback_repeated_upi(self):
        analysis = _fallback_analysis("UPI_TIMEOUT", retry_count=2, success_rate=0.60)
        self.assertEqual(analysis.recommended_action, "RECOMMEND_ALTERNATIVE_METHOD")

    def test_fallback_insufficient_balance(self):
        analysis = _fallback_analysis("INSUFFICIENT_BALANCE", retry_count=2, success_rate=0.20)
        self.assertEqual(analysis.recommended_action, "STOP_RECOVERY")

    def test_fallback_card_declined(self):
        analysis = _fallback_analysis("CARD_DECLINED", retry_count=0, success_rate=0.70)
        self.assertEqual(analysis.recommended_action, "CREATE_PAYMENT_LINK")


class TestRazorpayService(unittest.TestCase):
    """Test Razorpay test mode and mock link generation."""

    def test_payment_link_generation(self):
        link = create_payment_link("case_test", 1499.0, "Test User", "test@reva.io", "Demo link")
        self.assertTrue(link.get("success"))
        self.assertTrue(link.get("short_url").startswith("https://rzp.io/") or "checkout" in link.get("short_url"))
        self.assertTrue(bool(link.get("payment_link_id")))

    def test_mock_payment_verification(self):
        verify = verify_payment("case_test", "plink_mock_123")
        self.assertTrue(verify.get("success"))
        self.assertEqual(verify.get("status"), "paid")


class TestDatabaseAndMetrics(unittest.TestCase):
    """Test mock database queries and dashboard calculations."""

    def setUp(self):
        self.db = get_supabase()

    def test_database_has_seeded_records(self):
        customers = self.db.table("customers").select("id", count="exact").execute()
        transactions = self.db.table("transactions").select("id", count="exact").execute()
        cases = self.db.table("recovery_cases").select("id", count="exact").execute()

        self.assertGreaterEqual(customers.count, 120)
        self.assertGreaterEqual(transactions.count, 400)
        self.assertGreaterEqual(cases.count, 50)

    def test_dashboard_metrics_calculation(self):
        metrics = get_metrics()
        self.assertGreater(metrics.total_revenue_at_risk, 0)
        self.assertGreaterEqual(metrics.total_revenue_recovered, 0)
        self.assertGreater(metrics.total_cases, 0)

    def test_dashboard_analytics_distribution(self):
        analytics = get_analytics()
        self.assertGreater(len(analytics["cases_by_status"]), 0)
        self.assertGreater(len(analytics["failure_reason_distribution"]), 0)
        self.assertGreater(len(analytics["recovery_timeline"]), 0)


class TestDemoScenarios(unittest.TestCase):
    """Test live scenario execution pipeline."""

    def test_scenario_1_temporary_bank_failure(self):
        req = DemoScenarioRequest(scenario=1)
        res = run_demo_scenario(req)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("final_status"), "RECOVERED")

    def test_scenario_4_high_value_policy_gate(self):
        req = DemoScenarioRequest(scenario=4)
        res = run_demo_scenario(req)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("final_status"), "REQUIRES_HUMAN_APPROVAL")

    def test_custom_scenario_execution(self):
        req = CustomScenarioRequest(
            amount=85000,
            payment_method="CARD",
            failure_reason="CARD_DECLINED",
            customer_success_rate=0.9,
            retry_count=0,
            customer_name="Judge Custom User"
        )
        res = run_custom_scenario(req)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("final_status"), "REQUIRES_HUMAN_APPROVAL")


if __name__ == "__main__":
    unittest.main()
