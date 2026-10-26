from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from slowapi.errors import RateLimitExceeded

from app.api.v1.ats import router as ats_router

# Routers
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.dsa import router as dsa_router
from app.api.v1.health import router as health_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.job_descriptions import router as job_descriptions_router
from app.api.v1.resumes import router as resumes_router
from app.api.v1.users import router as users_router
from app.core.config import settings
from app.core.db import check_db_connection_with_retry
from app.core.errors import (
    AppError,
    app_error_handler,
    generic_error_handler,
    rate_limit_error_handler,
    validation_error_handler,
)
from app.core.logging import RequestIdMiddleware, logger
from app.core.ratelimit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Placement Copilot backend...")
    
    # Check DB connection with backoff
    try:
        await check_db_connection_with_retry()
        logger.info("Database connection successfully established.")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}. Starting backend in degraded mode (health checks and documentation available).")

    # Validate LLM provider in production
    if settings.APP_ENV == "production" and settings.LLM_PROVIDER.lower() == "fake":
        raise RuntimeError("LLM_PROVIDER cannot be configured to 'fake' in production environment")

    # Verify Gemini API configuration if key provided
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            models = list(client.models.list(config={"page_size": 20}))
            model_names = [m.name for m in models]
            target_model = f"models/{settings.GEMINI_MODEL}" if not settings.GEMINI_MODEL.startswith("models/") else settings.GEMINI_MODEL
            if any(target_model in m for m in model_names):
                logger.info(f"Verified Gemini model {settings.GEMINI_MODEL} is available.")
            else:
                logger.warning(f"Target model {settings.GEMINI_MODEL} not explicitly in list: {model_names[:5]}")
        except Exception as e:
            logger.warning(f"Could not verify Gemini model at startup: {e}")

    yield

    logger.info("Shutting down Placement Copilot backend...")

app = FastAPI(
    title="Placement Copilot API",
    description="AI-powered placement preparation platform for engineering candidates",
    version="0.1.0",
    docs_url="/docs" if settings.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if settings.ENABLE_API_DOCS else None,
    debug=settings.APP_ENV == "development",
    lifespan=lifespan,
)

# State & Rate Limiting
app.state.limiter = limiter

# Middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)
app.add_exception_handler(Exception, generic_error_handler)

# Register v1 Routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(dsa_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
app.include_router(job_descriptions_router, prefix="/api/v1")
app.include_router(ats_router, prefix="/api/v1")
app.include_router(interviews_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Placement Copilot API is running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
