from unittest.mock import MagicMock, patch
from services import resume_store


@patch("services.resume_store.get_supabase_client")
def test_create_resume(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "r1", "name": "My Resume"}
    ]
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [
        {"id": "r1"}
    ]

    result = resume_store.create_resume("user1", "My Resume")
    assert result["id"] == "r1"


@patch("services.resume_store.get_supabase_client")
def test_list_resumes(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "r1", "name": "Resume 1"},
        {"id": "r2", "name": "Resume 2"},
    ]

    result = resume_store.list_resumes("user1")
    assert len(result) == 2


@patch("services.resume_store.get_supabase_client")
def test_delete_resume(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "r1"}
    ]

    result = resume_store.delete_resume("user1", "r1")
    assert result is True


@patch("services.resume_store.get_supabase_client")
def test_delete_resume_not_found(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.delete.return_value.eq.return_value.eq.return_value.execute.return_value.data = []

    result = resume_store.delete_resume("user1", "nonexistent")
    assert result is False


@patch("services.resume_store.get_supabase_client")
def test_get_diff(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Mock get_version calls
    with patch("services.resume_store.get_version") as mock_get_version:
        mock_get_version.side_effect = [
            {"id": "v1", "content": "line1\nline2\nline3"},
            {"id": "v2", "content": "line1\nline2_changed\nline3"},
        ]

        diff = resume_store.get_diff("user1", "r1", "v1", "v2")
        assert "line2" in diff
        assert "line2_changed" in diff
