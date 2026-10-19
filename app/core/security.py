from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()

def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    return password_hash.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False

def create_access_token(subject: str | int) -> str:
    secret_key = settings.JWT_SECRET_KEY

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured.")
    
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
    
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=settings.JWT_ALGORITHM,
    )

def decode_access_token(token: str) -> dict[str, Any]:
    secret_key = settings.JWT_SECRET_KEY

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY must be configured")

    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[settings.JWT_ALGORITHM],
    )

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise jwt.InvalidTokenError("Missing or invalid subject")

    return payload
