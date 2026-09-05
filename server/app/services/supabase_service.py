"""Unified Database Client — automatically connects to real Supabase or local Mock database."""

import logging
import concurrent.futures
import re
import supabase._sync.client
from app.config import get_settings
from app.services.mock_database import get_mock_supabase

logger = logging.getLogger(__name__)

_real_client = None

# Ensure the Python Supabase SDK supports modern opaque secret keys (sb_secret_...)
# in addition to legacy JWT-format service_role keys.
_orig_match = supabase._sync.client.re.match


def _extended_key_match(pattern, string, *args, **kwargs):
    if isinstance(string, str) and (string.startswith("sb_secret_") or string.startswith("sb_publishable_")):
        return True
    return _orig_match(pattern, string, *args, **kwargs)


supabase._sync.client.re.match = _extended_key_match


def get_supabase():
    """Return real Supabase client if configured and tables exist, otherwise full in-memory mock client."""
    global _real_client
    settings = get_settings()

    if settings.is_supabase_active:
        if _real_client is False:
            return get_mock_supabase()
        if _real_client is None:
            try:
                from supabase import create_client
                client = create_client(settings.supabase_url, settings.supabase_service_role_key)

                # Test query with a 5-second timeout to verify connection and table existence
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        lambda: client.table("recovery_cases").select("id").limit(1).execute()
                    )
                    future.result(timeout=5.0)
                _real_client = client
                logger.info("[Database] Connected successfully to REAL Supabase instance at %s", settings.supabase_url)
                return _real_client
            except concurrent.futures.TimeoutError:
                logger.warning("[Database] Supabase connection timed out (>5s). Using full in-memory mock database.")
                _real_client = False
                return get_mock_supabase()
            except Exception as e:
                err_msg = str(e)
                if "PGRST205" in err_msg or "schema cache" in err_msg:
                    logger.warning(
                        "[Database] Authenticated with Supabase at %s, but required tables are missing from schema. "
                        "Apply 'supabase/migrations/001_initial_schema.sql' in the Supabase SQL Editor. "
                        "Falling back to local mock database.",
                        settings.supabase_url
                    )
                else:
                    logger.warning(
                        "[Database] Supabase verification failed (%s). Using full in-memory mock database.",
                        err_msg
                    )
                _real_client = False
                return get_mock_supabase()
        return _real_client

    return get_mock_supabase()
