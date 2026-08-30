"""Unified Database Client — automatically connects to real Supabase or local Mock database."""

import logging
from app.config import get_settings
from app.services.mock_database import get_mock_supabase

logger = logging.getLogger(__name__)

_real_client = None


def get_supabase():
    """Return real Supabase client if configured, otherwise full in-memory mock client."""
    global _real_client
    settings = get_settings()

    if settings.is_supabase_active:
        if _real_client is None:
            try:
                from supabase import create_client
                logger.info("[Database] Connecting to REAL Supabase instance at %s", settings.supabase_url)
                _real_client = create_client(settings.supabase_url, settings.supabase_service_role_key)
            except Exception as e:
                logger.error("[Database] Real Supabase connection failed (%s), falling back to mock.", e)
                return get_mock_supabase()
        return _real_client

    return get_mock_supabase()
