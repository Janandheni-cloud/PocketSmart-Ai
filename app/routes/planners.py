"""
Planner routes: home interior, party, and jewelry recommendation generation.
"""
import io
import json
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from ..db import get_connection
from ..schemas import HomeRequest, PartyRequest
from ..security import require_user
from ..services.recommendation_service import recommend

router = APIRouter()

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def save_history(user_id: int, planner: str, request_data: dict, result: dict) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO history (user_id, planner, request_json, response_json) "
        "VALUES (?, ?, ?, ?)",
        (user_id, planner, json.dumps(request_data), json.dumps(result)),
    )
    conn.commit()
    conn.close()


@router.post("/generate-home")
def generate_home(payload: HomeRequest, request: Request):
    user_id = require_user(request)
    data = payload.model_dump()
    result = recommend("home", data)
    save_history(user_id, "home", data, result)
    return result


@router.post("/generate-party")
def generate_party(payload: PartyRequest, request: Request):
    user_id = require_user(request)
    data = payload.model_dump()
    result = recommend("party", data)
    save_history(user_id, "party", data, result)
    return result


@router.post("/generate-jewelry")
async def generate_jewelry(
    request: Request,
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form(...),
    preferences: str = Form(""),
    outfit: Optional[UploadFile] = File(None),
):
    user_id = require_user(request)
    if budget <= 0:
        raise HTTPException(status_code=422, detail="Budget must be greater than zero")

    image_bytes = None
    image_mime = None

    if outfit and outfit.filename:
        if outfit.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=415, detail="Upload JPG, PNG or WEBP only")

        raw = await outfit.read()
        from ..config import settings

        max_bytes = settings.max_upload_mb * 1024 * 1024
        if len(raw) > max_bytes:
            raise HTTPException(
                status_code=413, detail=f"Image is too large (max {settings.max_upload_mb} MB)"
            )

        # Verify the upload is really a readable image before using it.
        try:
            from PIL import Image

            Image.open(io.BytesIO(raw)).verify()
        except Exception:
            raise HTTPException(status_code=422, detail="Uploaded file is not a valid image")

        image_bytes = raw
        image_mime = outfit.content_type

    data = {"budget": budget, "occasion": occasion, "style": style, "preferences": preferences}
    result = recommend("jewelry", data, image_bytes, image_mime)
    save_history(user_id, "jewelry", data, result)
    return result


@router.get("/recommendations-details/{history_id}")
def recommendation_details(history_id: int, request: Request):
    user_id = require_user(request)
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM history WHERE id = ? AND user_id = ?", (history_id, user_id)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return {
        "id": row["id"],
        "planner": row["planner"],
        "request": json.loads(row["request_json"]),
        "response": json.loads(row["response_json"]),
        "created_at": row["created_at"],
    }
