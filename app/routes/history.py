"""
Routes for listing a user's saved recommendation history.
"""
import json

from fastapi import APIRouter, Request

from ..db import get_connection
from ..security import require_user

router = APIRouter()


@router.get("/history")
def history(request: Request):
    user_id = require_user(request)
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, planner, request_json, response_json, created_at "
        "FROM history WHERE user_id = ? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": row["id"],
            "planner": row["planner"],
            "request": json.loads(row["request_json"]),
            "response": json.loads(row["response_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
