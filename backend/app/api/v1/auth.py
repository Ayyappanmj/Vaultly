import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import check_auth_rate_limit, get_current_active_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.category import Category
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

DEFAULT_SYSTEM_CATEGORIES = [
    ("Groceries", "shopping-cart", "#10b981"),
    ("Electronics", "laptop", "#3b82f6"),
    ("Home & Kitchen", "home", "#f59e0b"),
    ("Dining & Entertainment", "coffee", "#ec4899"),
    ("Utilities & Bills", "zap", "#8b5cf6"),
    ("Healthcare", "heart", "#ef4444"),
    ("Travel & Transport", "car", "#06b6d4"),
    ("Subscriptions", "repeat", "#6366f1"),
]


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def register(
    request: Request,
    body: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    check_auth_rate_limit(request)

    # Validate password strength
    pwd_err = validate_password_strength(body.password)
    if pwd_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=pwd_err)

    # Check if user already exists
    existing = db.execute(
        select(User).where(User.email == body.email.lower())
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    # Create new user
    user = User(
        email=body.email.lower(),
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    # Seed default categories for this user
    for name, icon, color in DEFAULT_SYSTEM_CATEGORIES:
        category = Category(
            user_id=user.id,
            name=name,
            icon=icon,
            color=color,
            is_system=True,
        )
        db.add(category)

    # Record audit log
    audit = AuditLog(
        user_id=user.id,
        action="AUTH_REGISTER",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        details="User registered successfully.",
    )
    db.add(audit)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    body: UserLoginRequest,
    db: Session = Depends(get_db),
):
    check_auth_rate_limit(request)

    user = db.execute(
        select(User).where(User.email == body.email.lower())
    ).scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Account is disabled."
        )

    # Generate tokens
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    raw_refresh = create_refresh_token()
    token_hash = hashlib.sha256(raw_refresh.encode("utf-8")).hexdigest()

    refresh_entity = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
        revoked=False,
    )
    db.add(refresh_entity)

    # Record audit log
    audit = AuditLog(
        user_id=user.id,
        action="AUTH_LOGIN",
        entity_type="user",
        entity_id=str(user.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(audit)
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    check_auth_rate_limit(request)
    token_hash = hashlib.sha256(body.refresh_token.encode("utf-8")).hexdigest()

    stored_token = db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).scalar_one_or_none()

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        )

    # REUSE DETECTION: If token was already revoked, revoke all tokens for this user!
    if stored_token.revoked:
        user_id = stored_token.user_id
        db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
        all_tokens = (
            db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id))
            .scalars()
            .all()
        )
        for t in all_tokens:
            t.revoked = True

        audit = AuditLog(
            user_id=user_id,
            action="AUTH_TOKEN_REUSE_DETECTED",
            entity_type="refresh_token",
            details="Revoked refresh token was reused! Revoked all sessions for user security.",
            ip_address=request.client.host if request.client else None,
        )
        db.add(audit)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Security breach detected: Revoked token was reused. All sessions terminated.",
        )

    # Check expiration
    now = datetime.now(timezone.utc)
    expires_at = stored_token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        stored_token.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired.",
        )

    # Issue new token pair (ROTATION)
    user = db.execute(
        select(User).where(User.id == stored_token.user_id)
    ).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive."
        )

    new_access = create_access_token({"sub": str(user.id), "email": user.email})
    new_raw_refresh = create_refresh_token()
    new_token_hash = hashlib.sha256(new_raw_refresh.encode("utf-8")).hexdigest()

    # Revoke old token and record replacement
    stored_token.revoked = True
    stored_token.replaced_by = new_token_hash

    # Save new refresh token
    new_token_entity = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.refresh_token_expire_days),
        revoked=False,
    )
    db.add(new_token_entity)
    db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    body: RefreshTokenRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(body.refresh_token.encode("utf-8")).hexdigest()
    stored_token = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    if stored_token:
        stored_token.revoked = True
        db.commit()

    return MessageResponse(message="Successfully logged out.")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user
