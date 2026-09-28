"""
Password hashing (PBKDF2-HMAC-SHA256) and JWT bearer-token authentication.
"""
import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import HTTPException, Request

from .config import settings

PBKDF2_ROUNDS = 310_000


def hash_password(password: str) -> str:
    """Hash a plaintext password into a self-describing string."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ROUNDS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, encoded: str) -> bool:
    """Check a plaintext password against a stored hash produced by hash_password()."""
    try:
        _, rounds, salt_b64, digest_b64 = encoded.split("$")
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    """Issue a signed JWT for the given user id."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def get_token(request: Request) -> Optional[str]:
    """Read the bearer token from the Authorization header, falling back to a cookie."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("access_token")


def require_user(request: Request) -> int:
    """FastAPI dependency-style helper: returns the authenticated user id or raises 401."""
    token = get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
