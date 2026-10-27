import os

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWN_DEV_SECRETS = {
    "dev-secret-key-at-least-32-chars-long!",
    "change-this-in-production-to-a-secure-random-string-at-least-32-chars",
}
KNOWN_DEV_JWT_SECRETS = {
    "dev-jwt-secret-at-least-32-chars-long!",
    "change-this-in-production-jwt-secret-key-at-least-32-chars",
}


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = Field(default="dev-secret-key-at-least-32-chars-long!")
    JWT_SECRET: str = Field(default="dev-jwt-secret-at-least-32-chars-long!")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str
    DATABASE_URL_DIRECT: str
    TEST_DATABASE_URL: str = ""

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    CORS_ORIGINS: str | list[str] = "http://localhost:5173,http://localhost:3000"
    LLM_DAILY_QUOTA: int = 40
    MAX_UPLOAD_MB: int = 5
    ENABLE_API_DOCS: bool | None = None
    LLM_PROVIDER: str = "auto"

    COOKIE_SAMESITE: str | None = None
    COOKIE_SECURE: bool | None = None

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @model_validator(mode="after")
    def resolve_defaults(self) -> "Settings":
        if self.ENABLE_API_DOCS is None:
            self.ENABLE_API_DOCS = self.APP_ENV != "production"
        if self.COOKIE_SAMESITE is None:
            self.COOKIE_SAMESITE = "none" if self.APP_ENV == "production" else "lax"
        else:
            self.COOKIE_SAMESITE = self.COOKIE_SAMESITE.lower()
        if self.COOKIE_SECURE is None:
            self.COOKIE_SECURE = self.APP_ENV == "production"
        return self


def validate_production_settings(s: Settings) -> None:
    """
    Validates that production environment configuration adheres to strict security guards.
    Refuses startup with a descriptive error naming the setting if any production guard is violated.
    Does not block startup in non-production environments.
    """
    if s.APP_ENV != "production":
        return

    if s.SECRET_KEY in KNOWN_DEV_SECRETS:
        raise RuntimeError("SECRET_KEY cannot use known development default in production")
    if len(s.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters in production")

    if s.JWT_SECRET in KNOWN_DEV_JWT_SECRETS:
        raise RuntimeError("JWT_SECRET cannot use known development default in production")
    if len(s.JWT_SECRET) < 32:
        raise RuntimeError("JWT_SECRET must be at least 32 characters in production")

    cors_list = s.CORS_ORIGINS if isinstance(s.CORS_ORIGINS, list) else [s.CORS_ORIGINS]
    for origin in cors_list:
        if origin == "*":
            raise RuntimeError("CORS_ORIGINS cannot contain wildcard '*' in production")
        if origin.startswith("http://"):
            raise RuntimeError(f"CORS_ORIGINS cannot contain insecure http:// origin '{origin}' in production")

    if s.LLM_PROVIDER.lower() == "fake":
        raise RuntimeError("LLM_PROVIDER cannot be configured to 'fake' in production environment")

    for setting_name, url in [("DATABASE_URL", s.DATABASE_URL), ("DATABASE_URL_DIRECT", s.DATABASE_URL_DIRECT)]:
        url_lower = url.lower()
        if "localhost" in url_lower or "127.0.0.1" in url_lower:
            raise RuntimeError(f"{setting_name} cannot point to localhost in production")

    if not s.GEMINI_API_KEY or not s.GEMINI_API_KEY.strip():
        raise RuntimeError("GEMINI_API_KEY cannot be empty in production")


settings = Settings()
