import logging

import pytest

from app.core.config import Settings, validate_production_settings


def make_valid_prod_settings(**kwargs) -> Settings:
    base = {
        "APP_ENV": "production",
        "SECRET_KEY": "a" * 32,
        "JWT_SECRET": "b" * 32,
        "DATABASE_URL": "postgresql+psycopg://user:pass@ep-prod-pooler.ap-southeast-1.aws.neon.tech/neondb",
        "DATABASE_URL_DIRECT": "postgresql+psycopg://user:pass@ep-prod.ap-southeast-1.aws.neon.tech/neondb",
        "GEMINI_API_KEY": "dummy-gemini-key",
        "LLM_PROVIDER": "gemini",
        "CORS_ORIGINS": ["https://placement-copilot.vercel.app"],
    }
    base.update(kwargs)
    return Settings(**base)


def test_dev_mode_allows_dev_settings():
    dev_settings = Settings(
        APP_ENV="development",
        SECRET_KEY="dev-secret-key-at-least-32-chars-long!",
        JWT_SECRET="dev-jwt-secret-at-least-32-chars-long!",
        DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://user:pass@localhost:5432/neondb",
        GEMINI_API_KEY="",
        LLM_PROVIDER="fake",
        CORS_ORIGINS=["http://localhost:5173", "*"],
    )
    # Must not raise in development
    validate_production_settings(dev_settings)


def test_production_valid_settings():
    prod_settings = make_valid_prod_settings()
    # Must not raise with valid production config
    validate_production_settings(prod_settings)


def test_guard_secret_key_default():
    s = make_valid_prod_settings(SECRET_KEY="dev-secret-key-at-least-32-chars-long!")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(s)

    s2 = make_valid_prod_settings(SECRET_KEY="change-this-in-production-to-a-secure-random-string-at-least-32-chars")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(s2)


def test_guard_secret_key_short():
    s = make_valid_prod_settings(SECRET_KEY="short-secret-key")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(s)


def test_guard_jwt_secret_default():
    s = make_valid_prod_settings(JWT_SECRET="dev-jwt-secret-at-least-32-chars-long!")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(s)

    s2 = make_valid_prod_settings(JWT_SECRET="change-this-in-production-jwt-secret-key-at-least-32-chars")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(s2)


def test_guard_jwt_secret_short():
    s = make_valid_prod_settings(JWT_SECRET="short-jwt-secret")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        validate_production_settings(s)


def test_guard_cors_wildcard():
    s = make_valid_prod_settings(CORS_ORIGINS=["*"])
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_production_settings(s)


def test_guard_cors_http():
    s = make_valid_prod_settings(CORS_ORIGINS=["http://insecure-domain.com"])
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        validate_production_settings(s)


def test_guard_llm_provider_fake():
    s = make_valid_prod_settings(LLM_PROVIDER="fake")
    with pytest.raises(RuntimeError, match="LLM_PROVIDER"):
        validate_production_settings(s)


def test_guard_database_url_localhost():
    s = make_valid_prod_settings(DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/neondb")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_settings(s)

    s_ip = make_valid_prod_settings(DATABASE_URL="postgresql+psycopg://user:pass@127.0.0.1:5432/neondb")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        validate_production_settings(s_ip)


def test_guard_database_url_direct_localhost():
    s = make_valid_prod_settings(DATABASE_URL_DIRECT="postgresql+psycopg://user:pass@localhost:5432/neondb")
    with pytest.raises(RuntimeError, match="DATABASE_URL_DIRECT"):
        validate_production_settings(s)

    s_ip = make_valid_prod_settings(DATABASE_URL_DIRECT="postgresql+psycopg://user:pass@127.0.0.1:5432/neondb")
    with pytest.raises(RuntimeError, match="DATABASE_URL_DIRECT"):
        validate_production_settings(s_ip)


def test_guard_gemini_api_key_empty():
    s = make_valid_prod_settings(GEMINI_API_KEY="")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        validate_production_settings(s)

    s_whitespace = make_valid_prod_settings(GEMINI_API_KEY="   ")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        validate_production_settings(s_whitespace)


def test_enable_api_docs_defaults():
    # Production defaults to False
    prod = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
    )
    assert prod.ENABLE_API_DOCS is False

    # Development defaults to True
    dev = Settings(
        APP_ENV="development",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
    )
    assert dev.ENABLE_API_DOCS is True

    # Explicit override in production
    prod_override = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
        ENABLE_API_DOCS=True,
    )
    assert prod_override.ENABLE_API_DOCS is True

    # Explicit override in development
    dev_override = Settings(
        APP_ENV="development",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
        ENABLE_API_DOCS=False,
    )
    assert dev_override.ENABLE_API_DOCS is False


def test_cookie_settings_defaults_and_overrides():
    # Production defaults: SameSite=None, Secure=True
    prod = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
    )
    assert prod.COOKIE_SAMESITE == "none"
    assert prod.COOKIE_SECURE is True

    # Development defaults: SameSite=lax, Secure=False
    dev = Settings(
        APP_ENV="development",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
    )
    assert dev.COOKIE_SAMESITE == "lax"
    assert dev.COOKIE_SECURE is False

    # Configurable override in production (e.g. COOKIE_SAMESITE=lax for same-domain proxy)
    prod_lax = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
        COOKIE_SAMESITE="lax",
    )
    assert prod_lax.COOKIE_SAMESITE == "lax"
    assert prod_lax.COOKIE_SECURE is True

    # Configurable override for COOKIE_SECURE
    dev_secure = Settings(
        APP_ENV="development",
        DATABASE_URL="postgresql+psycopg://pooler/neondb",
        DATABASE_URL_DIRECT="postgresql+psycopg://direct/neondb",
        COOKIE_SECURE=True,
    )
    assert dev_secure.COOKIE_SECURE is True


@pytest.mark.asyncio
async def test_cookie_samesite_none_without_https_warning(caplog):
    from fastapi import FastAPI

    from app.main import lifespan

    test_app = FastAPI(lifespan=lifespan)
    
    # In dev environment with SameSite=none and http CORS origin, verify startup logs warning
    from app.core import config
    orig_samesite = config.settings.COOKIE_SAMESITE
    orig_cors = config.settings.CORS_ORIGINS
    try:
        config.settings.COOKIE_SAMESITE = "none"
        config.settings.CORS_ORIGINS = ["http://localhost:5173"]
        with caplog.at_level(logging.WARNING):
            async with lifespan(test_app):
                pass
        assert any("SameSite=None is configured without an https origin" in rec.message for rec in caplog.records)
    finally:
        config.settings.COOKIE_SAMESITE = orig_samesite
        config.settings.CORS_ORIGINS = orig_cors
