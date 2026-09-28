"""
Gemini-backed recommendation generation, with:
  - automatic retries when Gemini is busy (503 / 429),
  - a backup model tried if the main model keeps failing,
  - a final fallback to built-in suggestions (see catalog.py).
"""
import json
import os
import re
import time
from typing import Optional

from ..config import settings
from .catalog import fallback, search_url

BACKUP_MODEL = os.getenv("GEMINI_BACKUP_MODEL", "gemini-3.5-flash")
ATTEMPTS_PER_MODEL = 3
WAIT_SECONDS = 2

SYSTEM_PROMPT = """You are PocketSmart AI, a budget-aware recommendation assistant.
Return ONLY valid JSON with keys: allocation, recommendations, tips.
Each item in "recommendations" must contain: name, category, platform, estimated_price, reason.
Do not claim live price or availability. Stay within the user's total budget.
This is planning assistance, not financial advice."""


def _build_prompt(planner: str, data: dict) -> str:
    return (
        f"{SYSTEM_PROMPT}\n"
        f"Planner: {planner}\n"
        f"Input: {json.dumps(data, ensure_ascii=False)}\n"
        "Create 4-8 practical recommendations. "
        "For 'home' use IKEA/Amazon/Flipkart; "
        "for 'party' use Swiggy/Zomato/OYO/Amazon; "
        "for 'jewelry' use Amazon/Flipkart."
    )


def _is_busy_error(error: Exception) -> bool:
    text = str(error)
    return "503" in text or "429" in text or "UNAVAILABLE" in text or "RESOURCE_EXHAUSTED" in text


def _call_gemini(client, types, model: str, contents: list):
    """Call Gemini, retrying a few times if the model is busy."""
    last_error = None
    for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.35,
                ),
            )
        except Exception as error:
            last_error = error
            print(f"GEMINI ERROR ({model}, try {attempt}/{ATTEMPTS_PER_MODEL}):", error)
            if not _is_busy_error(error):
                break
            if attempt < ATTEMPTS_PER_MODEL:
                time.sleep(WAIT_SECONDS * attempt)
    raise last_error


def generate(
    planner: str,
    data: dict,
    image_bytes: Optional[bytes] = None,
    image_mime: Optional[str] = None,
) -> dict:
    if not settings.gemini_api_key:
        print("GEMINI ERROR: no API key found in .env")
        return fallback(planner, data)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.gemini_api_key)
        prompt = _build_prompt(planner, data)

        contents = [prompt]
        if image_bytes:
            contents += [
                types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"),
                "Use the outfit image only for broad color/style coordination.",
            ]

        models_to_try = [settings.gemini_model]
        if BACKUP_MODEL and BACKUP_MODEL != settings.gemini_model:
            models_to_try.append(BACKUP_MODEL)

        response = None
        for model in models_to_try:
            try:
                response = _call_gemini(client, types, model, contents)
                break
            except Exception:
                print(f"GEMINI: giving up on model {model}")
        if response is None:
            return fallback(planner, data)

        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", response.text.strip(), flags=re.I)
        parsed = json.loads(text)

        budget = float(data["budget"])
        recommendations = []
        for item in parsed.get("recommendations", [])[:8]:
            recommendations.append(
                {
                    "name": str(item.get("name", "Suggested item")),
                    "category": str(item.get("category", "General")),
                    "platform": str(item.get("platform", "Amazon")),
                    "estimated_price": max(1, float(item.get("estimated_price", budget / 8))),
                    "reason": str(item.get("reason", "Fits the stated preferences and budget.")),
                    "search_url": "",
                }
            )

        if not recommendations:
            print("GEMINI ERROR: Gemini returned no recommendations")
            return fallback(planner, data)

        # Rescale so the total never exceeds the stated budget.
        total = sum(item["estimated_price"] for item in recommendations)
        if total > budget:
            factor = budget / total
            for item in recommendations:
                item["estimated_price"] = round(item["estimated_price"] * factor, 2)

        for item in recommendations:
            item["search_url"] = search_url(item["platform"], item["name"])

        return {
            "planner": planner,
            "budget": budget,
            "allocation": parsed.get("allocation", {}),
            "recommendations": recommendations,
            "tips": parsed.get("tips", [])[:6],
            "disclaimer": "AI-generated estimates are not live prices or guarantees.",
            "ai_used": True,
        }
    except Exception as e:
        print("GEMINI ERROR:", e)
        return fallback(planner, data)