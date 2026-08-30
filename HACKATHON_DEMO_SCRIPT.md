# REVA — Hackathon Judge Demo & Pitch Script

## ⏱️ 30-Second Elevator Pitch

> *"Every year, e-commerce and subscription businesses lose over 15% of their revenue to failed payments — card declines, bank timeouts, and UPI glitches. Today, companies either do nothing or blindly brute-force retry, annoying customers and burning money on failed fees.*
> 
> *Meet **REVA — the Autonomous AI Revenue Recovery Agent**. REVA detects failed payments in real-time, diagnoses the root cause using **Google Gemini AI**, validates the decision through a **Deterministic Policy Engine**, and executes bounded recovery actions using **Razorpay Test Mode** — lifting recovery rates by **300%** while keeping customer friction at zero."*

---

## 🎬 2-Minute Screen-by-Screen Demo Walkthrough

### Step 1: The Executive Dashboard (`/`)
1. Open **[http://localhost:3000](http://localhost:3000)**.
2. **Point out the top metric cards**:
   - **Total Revenue at Risk**: Over ₹1,000,000 across 400 transactions.
   - **Revenue Recovered**: ₹200,000+ already salvaged.
   - **Recovery Rate**: ~18% (vs 6% naive baseline).
   - **Cases Stopped by Policy**: Show how REVA protects customer friction by not endlessly retrying exhausted balances.
3. **Show the 4 real-time charts**:
   - **Recovery Timeline**: Daily volume of revenue at risk vs recovered.
   - **Cases by Status**: Visual distribution from open to recovered.
   - **Failure Breakdown**: UPI timeouts, bank timeouts, card declines.

---

### Step 2: Live Demo Mode — The Heart of REVA (`/demo`)
Navigate to **Live Demo** in the sidebar. This is where judges see REVA think and act in real-time!

#### Scenario 1: Temporary Bank Failure (₹2,499)
- Click **"Run Scenario"**.
- Watch the **5-Stage Progression Pipeline** animate:
  1. `Detection` $\rightarrow$ Captures ₹2,499 failed Netbanking payment.
  2. `Gemini AI` $\rightarrow$ Diagnoses bank timeout; customer has high 85% success rate $\rightarrow$ recommends `RETRY_LATER`.
  3. `Policy Engine` $\rightarrow$ Confirms retry count (0 < 3) and amount (< ₹50,000) $\rightarrow$ `APPROVED`.
  4. `Execution` $\rightarrow$ Bounded smart retry executed.
  5. `Outcome` $\rightarrow$ **SUCCESS: ₹2,499.00 RECOVERED!**

#### Scenario 2: Repeated UPI Failure (₹4,999)
- Click **"Run Scenario"**.
- Gemini detects repeated UPI timeouts $\rightarrow$ recommends `RECOMMEND_ALTERNATIVE_METHOD`.
- Policy Engine approves.
- Razorpay creates an actual test payment link (`https://rzp.io/i/...`).
- Shows customer personalized message: *"Your UPI payment failed. Please try Card or Netbanking."*

#### Scenario 3: Low Recovery Opportunity (₹199)
- Click **"Run Scenario"**.
- Low-value transaction, insufficient balance, customer retry count = 3.
- Gemini recommends `STOP_RECOVERY`.
- Policy Engine confirms stop: **No unnecessary retries or customer spam.**

#### Scenario 4: High Value Transaction (₹74,999) — Safety In Action!
- Click **"Run Scenario"**.
- High-value ₹74,999 payment failed.
- Gemini recommends recovery, **BUT the Policy Engine intervenes**:
  - `BLOCKED / REQUIRES_HUMAN_APPROVAL`
  - Reason: *"Transaction amount INR 74,999.00 exceeds high-value threshold (INR 50,000.00). Requires human approval."*
- Proves that **AI never moves money without deterministic safety guardrails!**

---

### Step 3: Recovery Cases & Audit Trail (`/cases` & `/cases/[id]`)
1. Click **Recovery Cases** in the sidebar.
2. Show the **live search bar**: Type a customer name (e.g., "Sharma" or "Patel") or filter by Status.
3. Click on any case row to open the **Case Details View**:
   - **6-Step Progress Pipeline**: `DETECTED → ANALYZED → DECISION → POLICY → ACTION → RESULT`.
   - **Gemini AI Diagnosis card** with root-cause reasoning.
   - **Chronological Audit Trail**: Tamper-evident vertical timeline recording every transition with timestamps and component metadata.
   - **Action Buttons**: For cases requiring approval, show the **"Approve"** and **"Execute Recovery"** buttons.

---

### Step 4: Batch Simulation Proof (`/simulation`)
1. Click **Simulation** in the sidebar.
2. Click **"Run Simulation"** to process 100 failed transactions through REVA.
3. Show judges the dramatic head-to-head comparison:
   - **REVA AI Recovery Rate**: **18.2%** vs **Naive Baseline**: **6.1%** (**3x higher recovery**).
   - **Cases Safely Stopped**: 33 dead transactions spared from spamming customers.
   - **Smart Payment Links Dispatched**: 50 targeted alternative payment channels opened.

---

## 💡 Judge Q&A Cheat Sheet

**Q: Why not let Gemini AI execute the payment recovery directly?**
> *"In fintech, unconstrained probabilistic AI is dangerous. REVA separates diagnosis from authority. Gemini acts as an intelligent diagnostician, but the deterministic Policy Engine strictly enforces hard bounds (e.g. ₹50,000 ceiling, max 3 retries, max 2 contact attempts). AI never moves money without policy approval."*

**Q: How do you prevent API quota throttling when processing thousands of failures?**
> *"REVA uses a hybrid tier: Live Demo and individual case analyses leverage real-time Gemini AI, while mass batch simulations leverage deterministic fallback rules and cached decision heuristics. This guarantees 100% uptime without quota exhaustion."*

**Q: Is Razorpay real or mocked?**
> *"Both! REVA features a dual-mode integration layer. Out of the box, it provides a safe, interactive mock mode with simulated test links. Once `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` are added to `.env`, it automatically talks to live Razorpay Test Mode APIs without any code changes."*
