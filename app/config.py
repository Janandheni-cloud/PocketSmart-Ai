"""
Application configuration.

All values can be overridden via environment variables or a `.env` file
placed in the `backend/` directory (see `.env.example`).
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/  (parent of the app/ package)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    app_name: str = os.getenv("APP_NAME", "PocketSmart AI")
    secret_key: str = os.getenv(
        "SECRET_KEY", "dev-secret-change-me-use-a-long-random-value"
    )
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    database_path: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "pocketsmart.db"))
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "120"))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "5"))


settings = Settings()
