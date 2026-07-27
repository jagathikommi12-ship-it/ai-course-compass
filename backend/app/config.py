from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All secrets come from environment variables — never hardcode keys.
    SUPABASE_SERVICE_ROLE_KEY bypasses RLS and must only ever be read here,
    on the server. It must never be sent to the React app, the Gradio app,
    or logged.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    # Only needed for projects still on Supabase's legacy shared HS256 secret.
    # Projects on the newer JWT Signing Keys system need nothing here at all —
    # verification fetches the public key from the project's own JWKS endpoint
    # instead (see app/auth.py).
    supabase_jwt_secret: str | None = None

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5"

    cors_allow_origins: str = "http://localhost:5173,http://localhost:7860"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
