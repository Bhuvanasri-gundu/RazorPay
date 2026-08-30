"""REVA — AI Revenue Recovery Agent — FastAPI Application."""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import dashboard, cases, demo, payments
from app.config import get_settings

logger = logging.getLogger("reva.startup")

app = FastAPI(
    title="REVA — AI Revenue Recovery Agent",
    description="AI-powered revenue recovery from failed payments",
    version="1.0.0",
)


@app.on_event("startup")
def startup_configuration_check():
    settings = get_settings()
    logger.info("==================================================")
    logger.info("  REVA -- Autonomous Revenue Recovery Agent")
    logger.info("  Configuration & Environment Verification")
    logger.info("==================================================")

    if settings.is_gemini_active:
        logger.info(f"[+] Google Gemini AI: CONFIGURED (Model: {settings.gemini_model})")
    else:
        logger.warning("[!] Gemini credentials are not configured. Using fallback analysis mode.")

    if settings.is_supabase_active:
        logger.info(f"[+] Supabase PostgreSQL: CONFIGURED ({settings.supabase_url})")
    else:
        logger.warning("[!] Supabase credentials are not configured. Database integration is using local/mock in-memory mode.")

    if settings.is_razorpay_active:
        logger.info(f"[+] Razorpay Test Mode: CONFIGURED (Key: {settings.razorpay_key_id[:8]}...)")
    else:
        logger.warning("[!] Razorpay credentials are not configured. Payment link creation is using simulated test links.")

    logger.info("==================================================")

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router)
app.include_router(cases.router)
app.include_router(demo.router)
app.include_router(payments.router)


@app.get("/")
def root():
    return {"name": "REVA", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
def health():
    """Health check endpoint displaying active operational modes."""
    settings = get_settings()
    return {
        "status": "healthy",
        "gemini": {
            "configured": settings.is_gemini_active,
            "mode": "real" if settings.is_gemini_active else "mock",
            "model": settings.gemini_model,
        },
        "database": {
            "configured": settings.is_supabase_active,
            "mode": "real_supabase" if settings.is_supabase_active else "mock_in_memory",
        },
        "razorpay": {
            "configured": settings.is_razorpay_active,
            "mode": "real_test" if settings.is_razorpay_active else "mock",
        },
    }


@app.post("/api/seed")
def seed_data():
    """Seed the database with synthetic data."""
    from app.seed import seed_database
    try:
        seed_database()
        return {"success": True, "message": "Database seeded successfully."}
    except Exception as e:
        return {"success": False, "error": str(e)}
