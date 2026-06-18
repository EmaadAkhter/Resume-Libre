from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException


@patch("services.auth.get_supabase_client")
def test_verify_jwt_valid(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@test.com"
    mock_client.auth.get_user.return_value = MagicMock(user=mock_user)

    from core.deps import verify_jwt
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="valid-token"
    )
    import asyncio

    result = asyncio.run(verify_jwt(credentials))

    assert result["id"] == "user-123"
    assert result["email"] == "test@test.com"


@patch("services.auth.get_supabase_client")
def test_verify_jwt_invalid(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.auth.get_user.return_value = MagicMock(user=None)

    from core.deps import verify_jwt
    from fastapi.security import HTTPAuthorizationCredentials

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid-token"
    )
    import asyncio

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(verify_jwt(credentials))

    assert exc_info.value.status_code == 401


@patch("services.auth.get_supabase_client")
def test_require_admin_passes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "role": "admin"
    }

    from core.deps import require_admin
    import asyncio

    user = {"id": "admin-123", "email": "admin@test.com", "role": "admin"}
    result = asyncio.run(require_admin(user))
    assert result["id"] == "admin-123"


@patch("services.auth.get_supabase_client")
def test_require_admin_fails_for_non_admin(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value.data = {
        "role": "user"
    }

    from core.deps import require_admin
    import asyncio

    user = {"id": "user-123", "email": "user@test.com", "role": "user"}
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(require_admin(user))

    assert exc_info.value.status_code == 403
