"""
Authentication routes: register, login, logout, and session lookups.
"""
from fastapi import APIRouter, HTTPException, Request

from ..db import get_connection
from ..schemas import LoginRequest, RegisterRequest
from ..security import create_access_token, hash_password, require_user, verify_password

router = APIRouter()


@router.post("/register")
def register(payload: RegisterRequest):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (payload.name.strip(), payload.email.lower().strip(), hash_password(payload.password)),
        )
        conn.commit()
        user_id = cursor.lastrowid
    except Exception:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    finally:
        conn.close()
    return {"message": "Registration successful", "access_token": create_access_token(user_id)}


@router.post("/login")
def login(payload: LoginRequest):
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (payload.email.lower().strip(),)
    ).fetchone()
    conn.close()
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful", "access_token": create_access_token(user["id"])}


@router.post("/token")
def token(payload: LoginRequest):
    """Alias for /login, useful for simple integrations/tests."""
    return login(payload)


@router.post("/logout")
def logout():
    # JWTs are stateless; the frontend simply discards the token.
    return {"message": "Logged out"}


@router.get("/session-info")
def session_info(request: Request):
    user_id = require_user(request)
    conn = get_connection()
    user = conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return {"authenticated": True, "user": dict(user)}


@router.get("/session-data")
def session_data(request: Request):
    user_id = require_user(request)
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, planner, created_at FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user_id,),
    ).fetchall()
    conn.close()
    return {"user_id": user_id, "history": [dict(row) for row in rows]}
