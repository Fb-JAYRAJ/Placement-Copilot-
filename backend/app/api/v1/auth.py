import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.errors import ConflictError, UnauthorizedError
from app.core.ratelimit import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    validate_password_strength,
    verify_password,
)
from app.models.models import ActivityEvent, RefreshToken, User
from app.schemas.auth import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

def _set_refresh_cookie(response: Response, raw_token: str):
    response.set_cookie(
        key="refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )

AUTH_RATE_LIMIT = "10/minute" if settings.APP_ENV == "production" else "60/minute"

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
async def register(
    request: Request,
    response: Response,
    payload: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    validate_password_strength(payload.password)
    
    # Check email duplicate
    stmt = select(User).where(User.email == payload.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise ConflictError("An account with this email already exists")

    hashed_pw = get_password_hash(payload.password)
    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hashed_pw,
        college=payload.college,
        grad_year=payload.grad_year,
        target_role=payload.target_role,
        target_companies=payload.target_companies or [],
    )
    db.add(user)
    await db.flush()

    # Log activity event
    event = ActivityEvent(
        user_id=user.id,
        type="account_created",
        title="Created Placement Copilot Account",
        detail={"email": user.email},
    )
    db.add(event)

    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    raw_refresh = create_refresh_token()
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        family_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(token_record)
    await db.commit()
    await db.refresh(user)

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
async def login(
    request: Request,
    response: Response,
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")

    access_token = create_access_token({"sub": str(user.id)})
    raw_refresh = create_refresh_token()
    token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        family_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(token_record)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_tokens(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        # Check Authorization or custom header fallback
        raw_token = request.headers.get("x-refresh-token")
    
    if not raw_token:
        raise UnauthorizedError("Refresh token missing")

    hashed = hash_refresh_token(raw_token)
    now = datetime.now(UTC)
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hashed,
    )
    token_record = (await db.execute(stmt)).scalar_one_or_none()
    if not token_record or token_record.expires_at <= now:
        raise UnauthorizedError("Invalid or expired refresh token")

    user_stmt = select(User).where(User.id == token_record.user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    if not user:
        raise UnauthorizedError("User no longer exists")

    # Grace period for token rotation race: 10 seconds
    GRACE_PERIOD_SECONDS = 10.0

    if token_record.revoked_at is not None:
        elapsed = (now - token_record.revoked_at).total_seconds()
        if elapsed <= GRACE_PERIOD_SECONDS and token_record.successor_token:
            # Within grace window: return the same successor token and fresh access token
            new_access_token = create_access_token({"sub": str(user.id)})
            _set_refresh_cookie(response, token_record.successor_token)
            return TokenResponse(
                access_token=new_access_token,
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse.model_validate(user),
            )
        else:
            # Reused outside grace window: token family compromised, revoke all tokens in family
            revoke_stmt = (
                update(RefreshToken)
                .where(
                    RefreshToken.family_id == token_record.family_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=now)
            )
            await db.execute(revoke_stmt)
            await db.commit()
            raise UnauthorizedError("Refresh token revoked or reused")

    # Normal rotation: revoke current token and save successor
    new_raw_refresh = create_refresh_token()
    token_record.revoked_at = now
    token_record.successor_token = new_raw_refresh

    new_token_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_raw_refresh),
        family_id=token_record.family_id,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_token_record)
    await db.commit()

    _set_refresh_cookie(response, new_raw_refresh)
    new_access_token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=new_access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    raw_token = request.cookies.get("refresh_token") or request.headers.get("x-refresh-token")
    if raw_token:
        hashed = hash_refresh_token(raw_token)
        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            RefreshToken.revoked_at.is_(None),
        )
        token_record = (await db.execute(stmt)).scalar_one_or_none()
        if token_record:
            token_record.revoked_at = datetime.now(UTC)
            await db.commit()

    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}
