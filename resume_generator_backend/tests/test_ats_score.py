"""ATS keyword score endpoint: JSON parsing robustness, retry, demo, auth."""

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

RESUME = (
    "\\documentclass{article}\\begin{document}"
    "Python developer with FastAPI, PostgreSQL, and Docker experience "
    "across five years of backend work on high-traffic services."
    "\\end{document}"
)
JD = "Backend engineer role: Python, Kubernetes, and FastAPI experience required."

VALID_PAYLOAD = {
    "match_percent": 72,
    "matched_keywords": ["Python", "FastAPI"],
    "missing_keywords": [
        {
            "keyword": "Kubernetes",
            "importance": "high",
            "suggestion": "Add any container orchestration work.",
        }
    ],
    "summary": "Good overlap on core skills; missing orchestration keywords.",
}


def _completion(content: str) -> MagicMock:
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = content
    completion.usage = MagicMock(prompt_tokens=100, completion_tokens=50)
    return completion


def _mock_llm(*replies: str) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.side_effect = [_completion(r) for r in replies]
    return client


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("ALLOW_DEMO_REQUESTS", raising=False)
    from main import app

    return TestClient(app)


@pytest.fixture
def auth_headers():
    with patch("services.auth.get_supabase_client") as mock_get_client:
        supabase = MagicMock()
        user = MagicMock()
        user.id = "user-1"
        user.email = "u@example.com"
        supabase.auth.get_user.return_value = MagicMock(user=user)
        mock_get_client.return_value = supabase
        yield {"Authorization": "Bearer good"}


def _post(client, headers=None, **overrides):
    body = {"resume_text": RESUME, "job_description": JD, **overrides}
    return client.post("/analyze-ats", json=body, headers=headers or {})


def test_clean_json_reply(client, auth_headers):
    llm = _mock_llm(json.dumps(VALID_PAYLOAD))
    with patch("services.ats_score._get_client", return_value=llm):
        response = _post(client, auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["match_percent"] == 72
    assert data["matched_keywords"] == ["Python", "FastAPI"]
    assert data["missing_keywords"][0]["keyword"] == "Kubernetes"
    assert data["missing_keywords"][0]["importance"] == "high"
    assert "summary" in data
    assert llm.chat.completions.create.call_count == 1


def test_fenced_json_reply(client, auth_headers):
    fenced = f"```json\n{json.dumps(VALID_PAYLOAD)}\n```"
    llm = _mock_llm(fenced)
    with patch("services.ats_score._get_client", return_value=llm):
        response = _post(client, auth_headers)

    assert response.status_code == 200
    assert response.json()["match_percent"] == 72


def test_malformed_then_valid_retries_once(client, auth_headers):
    llm = _mock_llm("Sorry, I cannot produce JSON.", json.dumps(VALID_PAYLOAD))
    with patch("services.ats_score._get_client", return_value=llm):
        response = _post(client, auth_headers)

    assert response.status_code == 200
    assert response.json()["match_percent"] == 72
    assert llm.chat.completions.create.call_count == 2


def test_both_replies_malformed_returns_502(client, auth_headers):
    llm = _mock_llm("not json", "still not json")
    with patch("services.ats_score._get_client", return_value=llm):
        response = _post(client, auth_headers)

    assert response.status_code == 502
    assert "unreadable" in response.json()["detail"]


def test_out_of_range_match_percent_retries_then_502(client, auth_headers):
    bad = json.dumps({**VALID_PAYLOAD, "match_percent": 140})
    llm = _mock_llm(bad, bad)
    with patch("services.ats_score._get_client", return_value=llm):
        response = _post(client, auth_headers)

    assert response.status_code == 502
    assert llm.chat.completions.create.call_count == 2


def test_demo_mode_serves_canned_result(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from main import app

    demo_client = TestClient(app)
    with patch("services.ats_score._get_client") as mock_get_client:
        response = _post(demo_client)  # no auth header

    assert response.status_code == 200
    data = response.json()
    assert data["match_percent"] == 78
    assert data["matched_keywords"]
    assert data["missing_keywords"]
    mock_get_client.assert_not_called()


def test_requires_auth_without_demo(client):
    response = _post(client)
    assert response.status_code == 401


def test_short_job_description_rejected(client, auth_headers):
    response = _post(client, auth_headers, job_description="too short")
    assert response.status_code == 422
