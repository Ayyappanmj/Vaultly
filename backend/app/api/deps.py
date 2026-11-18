import hashlib
import json
import uuid
from typing import Annotated, Any
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.models.idempotency import IdempotencyRecord
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    token_type: str = payload.get("type")
    if user_id_str is None or token_type != "access":
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.execute(select(User).where(User.id == user_uuid)).scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# In-memory token bucket rate limiter for auth routes
_rate_limit_cache: dict[str, list[float]] = {}


def check_auth_rate_limit(
    request: Request, limit: int = 10, window_seconds: int = 60
) -> None:
    """Enforces rate limiting on authentication attempts."""
    if settings.environment == "testing":
        return
    import time

    ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    timestamps = _rate_limit_cache.get(ip, [])

    # Keep only timestamps within window
    timestamps = [t for t in timestamps if now - t < window_seconds]

    if len(timestamps) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication attempts. Please try again later.",
        )

    timestamps.append(now)
    _rate_limit_cache[ip] = timestamps


def handle_idempotent_request(
    db: Session,
    user_id: uuid.UUID,
    endpoint: str,
    idempotency_key: str | None,
    payload: Any,
) -> tuple[IdempotencyRecord | None, dict | None]:
    """Checks if an idempotency key exists:
    - If exists with same request hash: return cached response
    - If exists with different request hash: raise 409 Conflict
    - If key is None: pass through
    """
    if not idempotency_key:
        return None, None

    # Compute hash of request payload
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    req_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

    existing = db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.key == idempotency_key,
            IdempotencyRecord.user_id == user_id,
        )
    ).scalar_one_or_none()

    if existing:
        if existing.request_hash != req_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key reused with different request payload.",
            )
        cached_body = json.loads(existing.response_body)
        return existing, cached_body

    # Return key and hash to be saved on completion
    record = IdempotencyRecord(
        key=idempotency_key,
        user_id=user_id,
        endpoint=endpoint,
        request_hash=req_hash,
        response_code=200,
        response_body="",
    )
    return record, None
