from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.config import get_settings

_bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    email: str | None


@lru_cache
def _jwks_client() -> PyJWKClient:
    settings = get_settings()
    # Supabase publishes the current signing key(s) at this well-known,
    # unauthenticated endpoint whenever a project uses the newer asymmetric
    # JWT Signing Keys system. Fetching/caching from here means verification
    # needs no shared secret at all, and key rotation on Supabase's side
    # "just works" without redeploying the backend.
    return PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """
    Verifies the Supabase-issued access token sent by the frontend/Gradio app
    as `Authorization: Bearer <token>`.

    Supabase projects sign session tokens one of two ways:
      - Newer projects (and any migrated to it): an asymmetric key (ES256/RS256)
        whose public half is published at /auth/v1/.well-known/jwks.json —
        verified here with no secret material on this server at all.
      - Older/legacy projects: a single shared HS256 secret
        (SUPABASE_JWT_SECRET), which has to be verified locally against that
        value since it isn't safe to publish.
    The token's header names which one was used, so this picks the right
    path automatically rather than requiring the operator to know which
    system their project is on.

    Every endpoint that touches per-user data (completed courses, chat)
    must depend on this and use the returned user_id for every Supabase
    query, rather than trusting any user_id passed in the request body.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = credentials.credentials
    settings = get_settings()

    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg") == "HS256":
            if not settings.supabase_jwt_secret:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token uses the legacy HS256 secret, but SUPABASE_JWT_SECRET isn't configured",
                )
            payload = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES256"],
                audience="authenticated",
            )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    return CurrentUser(user_id=user_id, email=payload.get("email"))
