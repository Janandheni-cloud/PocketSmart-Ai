"""
Single entry point used by the route handlers, so routes don't need to
know whether recommendations come from Gemini or the fallback catalog.
"""
from typing import Optional

from .gemini_service import generate


def recommend(
    planner: str,
    data: dict,
    image_bytes: Optional[bytes] = None,
    image_mime: Optional[str] = None,
) -> dict:
    return generate(planner, data, image_bytes, image_mime)
