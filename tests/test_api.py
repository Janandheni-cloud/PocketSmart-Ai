"""
Basic API tests. Run with:  pytest -q

Uses a temporary SQLite file so tests never touch your real pocketsmart.db.
"""
import os
import tempfile

os.environ["DATABASE_PATH"] = os.path.join(tempfile.gettempdir(), "pocketsmart_test.db")

from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app

init_db()
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_and_login():
    email = "test@example.com"
    register_response = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "secret123"},
    )
    # 409 if a previous test run already created this user - both are fine.
    assert register_response.status_code in (200, 409)

    login_response = client.post(
        "/api/auth/login", json={"email": email, "password": "secret123"}
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]


def test_protected_home_planner():
    login_response = client.post(
        "/api/auth/login", json={"email": "test@example.com", "password": "secret123"}
    )
    token = login_response.json()["access_token"]

    response = client.post(
        "/api/generate-home",
        headers={"Authorization": "Bearer " + token},
        json={"budget": 50000, "room": "Living Room", "style": "Modern", "items": "Sofa, lights"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "recommendations" in body
    assert body["ai_used"] is False  # no GEMINI_API_KEY set during tests


def test_home_planner_requires_auth():
    response = client.post(
        "/api/generate-home",
        json={"budget": 50000, "room": "Living Room", "style": "Modern", "items": "Sofa, lights"},
    )
    assert response.status_code == 401
