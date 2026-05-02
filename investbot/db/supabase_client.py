from functools import lru_cache
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
    return create_client(settings.supabase_url, settings.supabase_key)
