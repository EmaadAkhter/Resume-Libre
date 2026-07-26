"""Auth on the LLM/CPU-cost endpoints: 401 without a token, demo mode bypasses."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    from main import app

    return TestClient(app)


@pytest.mark.parametrize(
    "method,path,kwargs",
    [
        ("post", "/generate-resume", {"json": {"github_username": "octocat"}}),
        ("get", "/generate-resume-stream", {"params": {"github_username": "octocat"}}),
        (
            "post",
            "/export-resume",
            {"json": {"markdown_content": "# Test", "format": "latex"}},
        ),
        (
            "post",
            "/extract-resume",
            {"files": {"file": ("a.txt", b"hello", "text/plain")}},
        ),
    ],
)
def test_endpoints_require_auth(client, method, path, kwargs):
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    with patch("services.auth.get_supabase_client") as mock_get_client:
        supabase = MagicMock()
        supabase.auth.get_user.side_effect = Exception("invalid token")
        mock_get_client.return_value = supabase

        response = client.post(
            "/generate-resume",
            json={"github_username": "octocat"},
            headers={"Authorization": "Bearer forged"},
        )
    assert response.status_code == 401


def test_valid_token_reaches_handler(client):
    with patch("services.auth.get_supabase_client") as mock_get_client:
        supabase = MagicMock()
        user = MagicMock()
        user.id = "user-1"
        user.email = "u@example.com"
        supabase.auth.get_user.return_value = MagicMock(user=user)
        mock_get_client.return_value = supabase

        # Empty input → handler's own 400, proving auth passed
        response = client.post(
            "/generate-resume", json={}, headers={"Authorization": "Bearer good"}
        )
    assert response.status_code == 400


def test_demo_mode_bypasses_auth(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from main import app

    client = TestClient(app)
    response = client.post("/generate-resume", json={})
    assert response.status_code == 400  # handler 400, not auth 401


def test_demo_request_header_serves_fixture(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.setenv("ALLOW_DEMO_REQUESTS", "true")
    from main import app

    client = TestClient(app)
    response = client.post(
        "/generate-resume",
        json={"github_username": "octocat"},
        headers={"X-Demo-Mode": "true"},
    )
    assert response.status_code == 200
    assert "\\documentclass" in response.json()["resume"]


def test_demo_header_ignored_when_not_allowed(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("ALLOW_DEMO_REQUESTS", raising=False)
    from main import app

    client = TestClient(app)
    response = client.post(
        "/generate-resume",
        json={"github_username": "octocat"},
        headers={"X-Demo-Mode": "true"},
    )
    assert response.status_code == 401
