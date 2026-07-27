from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_service_client() -> Client:
    """
    Server-side Supabase client using the service_role key. This bypasses
    RLS, so it must only be used for operations the backend has already
    authorized itself (e.g. reading the shared catalog, or writing a row
    on behalf of a user whose JWT we've already verified). Never construct
    this client with a key that came from a request.
    """
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
