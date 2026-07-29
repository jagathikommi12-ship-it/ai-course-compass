from functools import lru_cache

import httpx
from supabase import Client, ClientOptions, create_client

from app.config import get_settings


@lru_cache
def get_service_client() -> Client:
    """
    Server-side Supabase client using the service_role key. This bypasses
    RLS, so it must only be used for operations the backend has already
    authorized itself (e.g. reading the shared catalog, or writing a row
    on behalf of a user whose JWT we've already verified). Never construct
    this client with a key that came from a request.

    This client is a singleton shared across every request, each running in
    its own FastAPI threadpool thread. HTTP/2 multiplexes many concurrent
    requests over one TCP connection, and httpx/httpcore's HTTP/2 state
    machine isn't safe under that many-threads-one-connection load — it
    intermittently raises httpx.ReadError ([Errno 35] Resource temporarily
    unavailable) once several requests land at the same instant. Forcing
    HTTP/1.1 gives each thread its own pooled connection instead, which is
    the well-tested path for a shared client under concurrent sync callers.
    """
    settings = get_settings()
    httpx_client = httpx.Client(
        http2=False,
        limits=httpx.Limits(max_connections=40, max_keepalive_connections=20),
    )
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=ClientOptions(httpx_client=httpx_client),
    )
