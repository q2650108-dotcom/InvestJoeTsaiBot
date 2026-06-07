from functools import lru_cache
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from supabase import Client
else:
    Client = Any


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    from supabase import create_client
    from investbot.config import get_settings

    settings = get_settings()
    runtime_role = os.getenv("INVESTBOT_SUPABASE_ROLE", "service").strip().lower()
    if runtime_role == "frontend" and settings.supabase_anon_key:
        key = settings.supabase_anon_key
    else:
        key = settings.supabase_service_key or settings.supabase_key or settings.supabase_anon_key
    if not key:
        raise ValueError("Supabase key is not configured.")
    return create_client(settings.supabase_url, key)
