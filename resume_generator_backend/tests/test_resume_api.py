from fastapi.testclient import TestClient
from unittest.mock import patch


@patch("services.auth.get_supabase_client")
def test_health_endpoint(mock_get_client):
    from main import app

    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("services.auth.get_supabase_client")
def test_root_endpoint(mock_get_client):
    from main import app

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data


@patch("services.auth.get_supabase_client")
def test_get_system_prompt(mock_get_client):
    from main import app

    client = TestClient(app)

    response = client.get("/get-system-prompt")
    assert response.status_code == 200
    assert "prompt" in response.json()


@patch("services.auth.get_supabase_client")
def test_generate_resume_requires_input(mock_get_client):
    from main import app

    client = TestClient(app)

    response = client.post("/generate-resume", json={})
    assert response.status_code == 400


@patch("services.auth.get_supabase_client")
def test_extract_resume_unsupported_format(mock_get_client):
    from main import app

    client = TestClient(app)

    # Test with unsupported file extension
    response = client.post(
        "/extract-resume",
        files={"file": ("test.xyz", b"content", "application/octet-stream")},
    )
    assert response.status_code == 400


@patch("services.auth.get_supabase_client")
def test_export_resume_invalid_format(mock_get_client):
    from main import app

    client = TestClient(app)

    response = client.post(
        "/export-resume", json={"markdown_content": "# Test", "format": "invalid"}
    )
    assert response.status_code == 422  # Pydantic validation error


@patch("services.auth.get_supabase_client")
def test_protected_resume_endpoints_require_auth(mock_get_client):
    from main import app

    client = TestClient(app)

    # Without auth header, should get 401 (missing bearer)
    response = client.get("/resumes")
    assert response.status_code == 401
