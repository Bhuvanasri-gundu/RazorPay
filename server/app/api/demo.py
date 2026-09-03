"""Demo scenarios and batch simulation API endpoints."""

import json
import os
import random
import time
import uuid
from fastapi import APIRouter, HTTPException
from app.services.supabase_service import get_supabase
from app.services.recovery_agent import create_recovery_case, analyze_case, execute_recovery
from app.models.schemas import DemoScenarioRequest, CustomScenarioRequest
from app.services.audit_service import log_event
from app.services.gemini_service import analyze_payment
from app.services.policy_engine import evaluate as evaluate_policy

router = APIRouter(tags=["Demo & Simulation"])


# Pre-defined demo scenario configurations
DEMO_SCENARIOS = {
    1: {
        "name": "Temporary Bank Failure",
        "description": "A bank timeout that can be recovered via retry",
        "amount": 2499,
        "payment_method": "NETBANKING",
        "failure_reason": "BANK_TIMEOUT",
        "customer_success_rate": 0.85,
        "retry_count": 0,
    },
    2: {
        "name": "Repeated UPI Failure",
        "description": "Multiple UPI failures — recommend alternative payment method",
        "amount": 4999,
        "payment_method": "UPI",
        "failure_reason": "UPI_TIMEOUT",
        "customer_success_rate": 0.60,
        "retry_count": 2,
    },
    3: {
        "name": "Low Recovery Opportunity",
        "description": "Low-value transaction with poor customer history — AI recommends stopping",
        "amount": 199,
        "payment_method": "WALLET",
        "failure_reason": "INSUFFICIENT_BALANCE",
        "customer_success_rate": 0.15,
        "retry_count": 3,
    },
    4: {
        "name": "High Value Transaction",
        "description": "High-value payment that requires human approval per policy",
        "amount": 74999,
        "payment_method": "CARD",
        "failure_reason": "CARD_DECLINED",
        "customer_success_rate": 0.90,
        "retry_count": 0,
    },
}


def _execute_scenario_flow(scenario: dict, scenario_id: str | int = 1):
    """Run a specific demo or custom scenario end-to-end and return step-by-step results."""
    steps = []

    try:
        # Step 1: Initialize
        steps.append({"step": "INIT", "status": "PROCESSING", "message": f"Starting scenario: {scenario['name']}"})

        # Try database connection
        db = None
        try:
            db = get_supabase()
        except Exception:
            db = None

        cust_name = scenario.get("customer_name") or f"Demo User {scenario_id}"
        demo_email = f"demo.scenario{scenario_id}@reva.test"

        if db:
            existing = db.table("customers").select("*").eq("email", demo_email).execute()

            if existing.data:
                customer = existing.data[0]
                db.table("customers").update({
                    "previous_success_rate": scenario["customer_success_rate"],
                    "name": cust_name,
                }).eq("id", customer["id"]).execute()
                customer["previous_success_rate"] = scenario["customer_success_rate"]
                customer["name"] = cust_name
            else:
                customer = db.table("customers").insert({
                    "name": cust_name,
                    "email": demo_email,
                    "phone": f"+919999900{abs(hash(str(scenario_id))) % 900 + 100:03d}",
                    "previous_success_rate": scenario["customer_success_rate"],
                }).execute().data[0]

            txn = db.table("transactions").insert({
                "customer_id": customer["id"],
                "amount": scenario["amount"],
                "currency": "INR",
                "payment_method": scenario["payment_method"],
                "status": "FAILED",
                "failure_reason": scenario["failure_reason"],
                "retry_count": scenario["retry_count"],
            }).execute().data[0]

            case = create_recovery_case(txn["id"], customer["id"], scenario["amount"])
            case_id = case["id"]
        else:
            # Standalone simulated demo mode (no active DB connection)
            customer = {
                "id": str(uuid.uuid4()),
                "name": cust_name,
                "email": demo_email,
                "previous_success_rate": scenario["customer_success_rate"],
            }
            txn = {
                "id": str(uuid.uuid4()),
                "amount": scenario["amount"],
                "currency": "INR",
                "payment_method": scenario["payment_method"],
                "status": "FAILED",
                "failure_reason": scenario["failure_reason"],
                "retry_count": scenario["retry_count"],
            }
            case_id = str(uuid.uuid4())
            case = {"id": case_id, "amount_at_risk": scenario["amount"]}
            log_event(case_id, "Revenue Loss Detector", "CASE_CREATED",
                      f"Failed payment detected. Recovery case created. Amount at risk: INR {scenario['amount']:,.2f}")

        steps.append({
            "step": "CUSTOMER_FOUND",
            "status": "COMPLETED",
            "message": f"Customer: {customer['name']}",
            "data": {"customer_id": customer["id"]},
        })

        steps.append({
            "step": "PAYMENT_FAILED",
            "status": "COMPLETED",
            "message": f"Failed payment: INR {scenario['amount']:,.2f} via {scenario['payment_method']} — {scenario['failure_reason']}",
            "data": {"transaction_id": txn["id"]},
        })

        steps.append({
            "step": "CASE_CREATED",
            "status": "COMPLETED",
            "message": f"Recovery case created. Revenue at risk: INR {scenario['amount']:,.2f}",
            "data": {"case_id": case_id},
        })

        # Step 4: AI Analysis
        steps.append({"step": "AI_ANALYZING", "status": "PROCESSING", "message": "Gemini AI analyzing failure..."})

        if db:
            analysis = analyze_case(case_id)
        else:
            analysis_obj = analyze_payment(
                case_id=case_id,
                amount=scenario["amount"],
                payment_method=scenario["payment_method"],
                failure_reason=scenario["failure_reason"],
                retry_count=scenario["retry_count"],
                customer_success_rate=scenario["customer_success_rate"],
            )
            analysis = {
                "diagnosis": analysis_obj.diagnosis,
                "confidence": analysis_obj.confidence,
                "recommended_action": analysis_obj.recommended_action,
                "reason": analysis_obj.reason,
                "customer_message": analysis_obj.customer_message,
            }

        steps.append({
            "step": "AI_COMPLETE",
            "status": "COMPLETED",
            "message": f"Diagnosis: {analysis['diagnosis']}",
            "data": {
                "diagnosis": analysis["diagnosis"],
                "confidence": analysis["confidence"],
                "recommended_action": analysis["recommended_action"],
                "reason": analysis["reason"],
                "customer_message": analysis.get("customer_message"),
            },
        })

        # Step 5: Policy + Execution
        steps.append({"step": "POLICY_CHECK", "status": "PROCESSING", "message": "Policy Engine validating..."})

        if db:
            execution = execute_recovery(case_id)
        else:
            policy_decision = evaluate_policy(
                case_id=case_id,
                recommended_action=analysis["recommended_action"],
                retry_count=scenario["retry_count"],
                amount=scenario["amount"],
                contact_attempts=0,
            )
            if policy_decision.status in ("BLOCKED", "STOPPED_BY_POLICY", "REQUIRES_HUMAN_APPROVAL"):
                execution = {
                    "case_id": case_id,
                    "status": policy_decision.status,
                    "policy": {"status": policy_decision.status, "reason": policy_decision.reason},
                }
            elif analysis["recommended_action"] == "RETRY_LATER":
                execution = {
                    "case_id": case_id,
                    "status": "RECOVERED",
                    "recovered_amount": scenario["amount"],
                }
            elif analysis["recommended_action"] in ("CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD"):
                execution = {
                    "case_id": case_id,
                    "status": "PAYMENT_LINK_CREATED",
                    "payment_link_url": "https://rzp.io/i/reva_demo_link",
                    "message": "Razorpay payment link created",
                }
            elif analysis["recommended_action"] == "STOP_RECOVERY":
                execution = {
                    "case_id": case_id,
                    "status": "STOPPED",
                    "message": "Recovery stopped per policy validation",
                }
            else:
                execution = {"case_id": case_id, "status": "ESCALATED"}

        # Determine final status and step
        final_status = execution.get("status", "UNKNOWN")

        if final_status == "RECOVERED":
            steps.append({
                "step": "POLICY_APPROVED",
                "status": "COMPLETED",
                "message": "Action approved by Policy Engine",
            })
            steps.append({
                "step": "ACTION_EXECUTED",
                "status": "COMPLETED",
                "message": f"Recovery action executed: {analysis['recommended_action']}",
            })
            steps.append({
                "step": "RECOVERED",
                "status": "COMPLETED",
                "message": f"SUCCESS: INR {execution.get('recovered_amount', scenario['amount']):,.2f} RECOVERED!",
                "data": execution,
            })
        elif final_status == "PAYMENT_LINK_CREATED":
            steps.append({
                "step": "POLICY_APPROVED",
                "status": "COMPLETED",
                "message": "Action approved by Policy Engine",
            })
            steps.append({
                "step": "PAYMENT_LINK",
                "status": "COMPLETED",
                "message": "Razorpay payment link created",
                "data": execution,
            })
        elif final_status == "ALTERNATIVE_RECOMMENDED":
            steps.append({
                "step": "POLICY_APPROVED",
                "status": "COMPLETED",
                "message": "Action approved by Policy Engine",
            })
            steps.append({
                "step": "ALTERNATIVE",
                "status": "COMPLETED",
                "message": execution.get("message", "Alternative method recommended"),
                "data": execution,
            })
        elif final_status == "STOPPED":
            steps.append({
                "step": "POLICY_APPROVED",
                "status": "COMPLETED",
                "message": "AI recommends stopping. Policy confirms.",
            })
            steps.append({
                "step": "STOPPED",
                "status": "COMPLETED",
                "message": "Recovery stopped. No further action needed.",
                "data": execution,
            })
        elif final_status == "STOPPED_BY_POLICY":
            policy_data = execution.get("policy", {})
            steps.append({
                "step": "POLICY_BLOCKED",
                "status": "BLOCKED",
                "message": f"STOPPED: {policy_data.get('reason', 'Blocked by policy')}",
                "data": execution,
            })
        elif final_status == "REQUIRES_HUMAN_APPROVAL":
            policy_data = execution.get("policy", {})
            steps.append({
                "step": "REQUIRES_APPROVAL",
                "status": "BLOCKED",
                "message": f"APPROVAL REQUIRED: {policy_data.get('reason', 'Requires human approval')}",
                "data": execution,
            })
        elif final_status == "RECOVERY_FAILED":
            steps.append({
                "step": "POLICY_APPROVED",
                "status": "COMPLETED",
                "message": "Action approved by Policy Engine",
            })
            steps.append({
                "step": "RECOVERY_FAILED",
                "status": "FAILED",
                "message": "Recovery attempt failed. Payment not recovered.",
                "data": execution,
            })
        else:
            steps.append({
                "step": "RESULT",
                "status": "COMPLETED",
                "message": f"Result: {final_status}",
                "data": execution,
            })

        return {
            "success": True,
            "scenario": scenario,
            "case_id": case_id,
            "steps": steps,
            "final_status": final_status,
        }

    except Exception as e:
        steps.append({
            "step": "ERROR",
            "status": "FAILED",
            "message": f"Error: {str(e)}",
        })
        return {
            "success": False,
            "scenario": scenario,
            "steps": steps,
            "error": str(e),
        }


@router.post("/api/demo/run-scenario")
def run_demo_scenario(req: DemoScenarioRequest):
    """Run a specific predefined demo scenario end-to-end and return step-by-step results."""
    scenario = DEMO_SCENARIOS.get(req.scenario)
    if not scenario:
        raise HTTPException(status_code=400, detail=f"Invalid scenario: {req.scenario}")
    return _execute_scenario_flow(scenario, req.scenario)


@router.post("/api/demo/run-custom")
@router.post("/api/demo/run-custom-scenario")
def run_custom_scenario(req: CustomScenarioRequest):
    """Run an interactive custom scenario with user-defined parameters."""
    scenario = {
        "name": f"Custom Simulation ({req.payment_method})",
        "description": f"Custom recovery test for {req.customer_name} ({req.failure_reason})",
        "amount": req.amount,
        "payment_method": req.payment_method,
        "failure_reason": req.failure_reason,
        "customer_success_rate": req.customer_success_rate,
        "retry_count": req.retry_count,
        "customer_name": req.customer_name or "Custom User",
    }
    return _execute_scenario_flow(scenario, "custom")


@router.post("/api/simulation/run-batch")
def run_batch_simulation():
    """Process failed transactions through REVA, comparing against baseline strategy."""
    db = None
    try:
        db = get_supabase()
    except Exception:
        db = None

    if db:
        return _run_db_batch_simulation(db)
    else:
        return _run_synthetic_file_batch_simulation()


def _run_db_batch_simulation(db):
    """Run simulation using connected Supabase database."""
    all_failed = db.table("transactions").select("*").eq("status", "FAILED").execute()
    failed_txns = all_failed.data or []

    existing_cases = db.table("recovery_cases").select("transaction_id").execute()
    existing_txn_ids = {c["transaction_id"] for c in (existing_cases.data or [])}
    unprocessed = [t for t in failed_txns if t["id"] not in existing_txn_ids]

    if not unprocessed:
        return _get_batch_stats(db)

    batch = unprocessed[:100]
    return _process_simulation_txns(batch, is_db=True)


def _run_synthetic_file_batch_simulation():
    """Run simulation using data/synthetic_data.json if database is not configured."""
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_data.json"))
    if not os.path.exists(data_path):
        data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "synthetic_data.json"))

    if not os.path.exists(data_path):
        from scripts.generate_data import generate_synthetic_dataset
        dataset = generate_synthetic_dataset(120, 400)
    else:
        with open(data_path, "r", encoding="utf-8") as f:
            dataset = json.load(f)

    failed_txns = [t for t in dataset.get("transactions", []) if t["status"] == "FAILED"]
    batch = failed_txns[:100]
    return _process_simulation_txns(batch, is_db=False)


def _process_simulation_txns(batch, is_db=False):
    """Core simulation computation comparing REVA vs baseline."""
    results = []
    retries = 0
    links_created = 0
    stopped = 0
    recovered_total = 0
    risk_total = 0

    from app.services.gemini_service import _fallback_analysis
    from app.services.policy_engine import evaluate as evaluate_policy

    for i, txn in enumerate(batch):
        try:
            amount = txn["amount"]
            risk_total += amount
            reason = txn.get("failure_reason") or "BANK_TIMEOUT"
            retry_count = txn.get("retry_count", 0)

            # Analyze (deterministic fallback for batch to avoid API quotas)
            analysis = _fallback_analysis(reason, retry_count, 0.7)
            action = analysis.recommended_action

            # Evaluate policy
            decision = evaluate_policy(
                case_id=f"sim_{i}",
                recommended_action=action,
                retry_count=retry_count,
                amount=amount,
            )

            if decision.status != "APPROVED":
                status = decision.status
                stopped += 1
                rec_amount = 0
            elif action == "RETRY_LATER":
                # Simulated recovery probability
                rec_amount = amount if random.random() < 0.65 else 0
                status = "RECOVERED" if rec_amount > 0 else "RECOVERY_FAILED"
                if status == "RECOVERED":
                    recovered_total += rec_amount
                retries += 1
            elif action in ("CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD"):
                rec_amount = amount if random.random() < 0.50 else 0
                status = "RECOVERED" if rec_amount > 0 else "PAYMENT_LINK_CREATED"
                if status == "RECOVERED":
                    recovered_total += rec_amount
                links_created += 1
            else:
                status = "STOPPED"
                stopped += 1
                rec_amount = 0

            results.append({
                "transaction_id": txn.get("id") or txn.get("temp_customer_id") or f"txn_{i+1}",
                "amount": amount,
                "failure_reason": reason,
                "recommended_action": action,
                "final_status": status,
                "recovered_amount": rec_amount,
            })
        except Exception as e:
            results.append({
                "transaction_id": f"txn_{i+1}",
                "error": str(e),
                "final_status": "ERROR",
            })

    # Baseline: Naive retry of all failed transactions
    baseline_recovered = sum(
        t["amount"] * 0.40 for t in batch if t.get("failure_reason") in ("BANK_TIMEOUT", "TECHNICAL_FAILURE")
    )
    baseline_rate = (baseline_recovered / risk_total * 100) if risk_total > 0 else 0.0
    reva_rate = (recovered_total / risk_total * 100) if risk_total > 0 else 0.0

    return {
        "total_processed": len(batch),
        "total_revenue_at_risk": risk_total,
        "total_recovered": recovered_total,
        "recovery_rate": round(reva_rate, 1),
        "cases_stopped": stopped,
        "payment_links_created": links_created,
        "retries_performed": retries,
        "baseline_recovery_rate": round(baseline_rate, 1),
        "reva_recovery_rate": round(reva_rate, 1),
        "cases": results[:20],
    }


def _get_batch_stats(db):
    """Get stats from existing processed cases."""
    cases = db.table("recovery_cases").select("*").execute()
    case_list = cases.data or []

    risk = sum(c["amount_at_risk"] for c in case_list)
    recovered = sum(c.get("recovered_amount", 0) or 0 for c in case_list)
    stopped = sum(1 for c in case_list if c["status"] in ("STOPPED", "STOPPED_BY_POLICY"))

    actions = db.table("recovery_actions").select("action_type").execute()
    action_list = actions.data or []
    retries = sum(1 for a in action_list if a["action_type"] == "RETRY_LATER")
    links = sum(1 for a in action_list if a["action_type"] in ("CREATE_PAYMENT_LINK", "RECOMMEND_ALTERNATIVE_METHOD"))

    rate = (recovered / risk * 100) if risk > 0 else 0
    baseline = rate * 0.4

    return {
        "total_processed": len(case_list),
        "total_revenue_at_risk": risk,
        "total_recovered": recovered,
        "recovery_rate": round(rate, 1),
        "cases_stopped": stopped,
        "payment_links_created": links,
        "retries_performed": retries,
        "baseline_recovery_rate": round(baseline, 1),
        "reva_recovery_rate": round(rate, 1),
        "cases": [],
        "message": "All failed transactions already processed. Showing existing stats.",
    }
