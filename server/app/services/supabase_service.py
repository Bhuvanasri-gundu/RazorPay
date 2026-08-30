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
        if _real_client is False:
            return get_mock_supabase()
        if _real_client is None:
            try:
                from supabase import create_client
                client = create_client(settings.supabase_url, settings.supabase_service_role_key)
                # Test query to verify connection and credentials
                client.table("recovery_cases").select("id").limit(1).execute()
                _real_client = client
                logger.info("[Database] Connected successfully to REAL Supabase instance at %s", settings.supabase_url)
            except Exception as e:
                logger.warning("[Database] Supabase credentials verification failed (%s). Using full in-memory mock database.", e)
                _real_client = False
                return get_mock_supabase()
        return _real_client

    return get_mock_supabase()
