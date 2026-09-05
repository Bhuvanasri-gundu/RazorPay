"""Unified Database Client — automatically connects to real Supabase or local Mock database."""

import logging
import concurrent.futures
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
                # Test query with a 5-second timeout to avoid blocking on slow/unreachable Supabase
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        lambda: client.table("recovery_cases").select("id").limit(1).execute()
                    )
                    future.result(timeout=5.0)
                _real_client = client
                logger.info("[Database] Connected successfully to REAL Supabase instance at %s", settings.supabase_url)
            except concurrent.futures.TimeoutError:
                logger.warning("[Database] Supabase connection timed out (>5s). Using full in-memory mock database.")
                _real_client = False
                return get_mock_supabase()
            except Exception as e:
                logger.warning("[Database] Supabase credentials verification failed (%s). Using full in-memory mock database.", e)
                _real_client = False
                return get_mock_supabase()
        return _real_client

    return get_mock_supabase()
