# REVA — Autonomous AI Revenue Recovery Agent

> Intelligent, autonomous recovery for failed e-commerce and SaaS payments. Powered by **FastAPI**, **Next.js 16**, **Google Gemini AI**, **Deterministic Policy Engine**, **Supabase PostgreSQL**, and **Razorpay Test Mode**.

---

## 📁 Repository Structure

```text
RazorPay/
├── dashboard/                 # Next.js 16 Dark Fintech Frontend
│   ├── app/                   # App Router pages (Dashboard, Cases, Live Demo, Simulation)
│   ├── components/            # Reusable UI widgets & status badges
│   ├── services/              # API communication layer
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility functions & styling helpers
│   ├── public/                # Static assets & brand icons
│   ├── package.json           # Frontend dependencies
│   ├── .env.local             # Local frontend environment configuration
│   └── .env.example           # Example frontend environment template
│
├── server/                    # FastAPI Backend Application
│   ├── app/
│   │   ├── main.py            # Application entrypoint & CORS configuration
│   │   ├── config.py          # Centralized Pydantic Settings & mode detection
│   │   ├── api/               # REST API endpoints (cases, dashboard, demo, payments)
│   │   ├── services/          # Business logic (Gemini, Policy Engine, Razorpay, Recovery Workflow, Database)
│   │   ├── models/            # Pydantic schemas & response models
│   │   ├── data/              # Pre-seeded synthetic transaction datasets
│   │   └── utils/             # Formatting & currency helpers
│   ├── tests/                 # Automated unittest suite (18 test cases)
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Server environment variables (placeholders ready)
│   └── .env.example           # Example server environment template
│
├── supabase/                  # Database Schema & Migrations
│   ├── migrations/            # SQL migration scripts
│   └── seed.sql               # Base database schema & initialization
│
├── README.md                  # Project documentation
└── .gitignore                 # Secure Git exclusion rules
```

---

## 🌟 Core Workflow & Safety Principle

```
FAILED PAYMENT
      ↓
DETECT REVENUE AT RISK (Revenue Loss Detector)
      ↓
GEMINI AI ANALYSIS (Diagnosis & Explainable Recommendation)
      ↓
POLICY ENGINE VALIDATION (Deterministic Safety Bounds: Max Retries, ₹50k Approval)
      ↓
RECOVERY EXECUTION (Smart Retry / Razorpay Payment Link / Alt Method / Stop)
      ↓
AUDIT TRAIL LOGGED → DASHBOARD UPDATED
```

> **Fintech Control Principle**: Gemini AI diagnoses and recommends; the **Deterministic Policy Engine** validates and governs. AI never moves money without policy approval.

---

## ⚡ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16 (Turbopack), React 19, Tailwind CSS v4, Recharts, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| **AI Diagnosis** | Official Google GenAI SDK (`gemini-2.0-flash`) with Deterministic Mock Fallback |
| **Policy Engine** | Rule-based engine (`MAX_RETRIES=3`, `HIGH_VALUE_THRESHOLD=₹50,000`) |
| **Database** | Supabase PostgreSQL + Auto-Mock in-memory database pre-seeded with 400 transactions |
| **Payments** | Razorpay Test Mode + Simulated test payment links |

---

## Screenshots

### 1. Main Dashboard
![REVA Dashboard](docs/screenshots/dashboard.png)

### 2. Recovery Case Details & Policy Workflow
![Recovery Case Details and Workflow](docs/screenshots/recovery-workflow.png)

### 3. Live Demo — Autonomous AI Diagnosis & Policy Decision
![Live Demo Execution](docs/screenshots/live-demo.png)

### 4. Razorpay Test Mode Checkout Flow
![Razorpay Test Checkout](docs/screenshots/razorpay-checkout.png)

---

## 🚀 Quick Start (Zero Setup Required for Demo)

The project includes an **automatic mock mode**. You can run and demo the full application immediately without any external API keys!

### 1. Start the Backend Server
```bash
cd server
python -m uvicorn app.main:app --reload --port 8000
```
- API Docs (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Status: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Start the Frontend Client
```bash
cd dashboard
npm run dev
```
- Open Web Application: [http://localhost:3000](http://localhost:3000)

### 3. Run Automated Tests
```bash
cd server
python -m unittest tests/test_reva_core.py
```

---

## 🔌 Switching to Live Mode (Gemini, Supabase, Razorpay)

When you are ready to connect real credentials, open **`server/.env`** and replace the placeholders:

```env
DATABASE_MODE=supabase
AI_MODE=gemini
PAYMENT_MODE=razorpay

# 1. Google Gemini AI (https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash

# 2. Supabase PostgreSQL (https://supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# 3. Razorpay Test Mode (https://dashboard.razorpay.com)
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_MODE=test
```

**Restart the backend**, and REVA will automatically switch each service from Mock to Real with **zero code changes**!

---

## 📊 Pages & Capabilities

1. **Dashboard (`/`)**: Real-time revenue at risk, recovered amount, recovery rate, timeline area chart, failure distribution, and action breakdown.
2. **Recovery Cases (`/cases`)**: Filterable cases table with instant live search (customer name, email, failure code), pagination, and status badges.
3. **Case Details (`/cases/[id]`)**: 6-stage workflow progress bar, transaction summary, AI diagnosis, recovery action executor, and chronological audit trail.
4. **Live Demo & Sandbox (`/demo`)**: 4 predefined scenario cards + interactive custom transaction sandbox with real-time 5-stage progress pipeline (`WAITING`, `PROCESSING`, `COMPLETED`, `BLOCKED`, `FAILED`).
5. **Batch Simulation (`/simulation`)**: Direct head-to-head comparison demonstrating **REVA AI (18.2% recovery)** vs **Naive Baseline (6.1% recovery)** on 100 failed transactions, with one-click JSON report export.

