from unittest.mock import MagicMock, patch
from services import template_store


@patch("services.template_store.get_supabase_client")
def test_list_templates_non_admin(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    mock_client.table.return_value.select.return_value.or_.return_value.order.return_value.execute.return_value.data = [
        {"id": "t1", "name": "Public MD", "is_public": True, "is_admin_only": False},
    ]
    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = [
        {"id": "t2", "name": "My Template", "is_public": False, "created_by": "user1"},
    ]

    result = template_store.list_templates("user1", is_admin=False)
    assert len(result) == 2


@patch("services.template_store.get_supabase_client")
def test_create_template(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client
    mock_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "t1", "name": "New Template"}]

    result = template_store.create_template("user1", "New Template", "# Content", "md")
    assert result["id"] == "t1"


@patch("services.template_store.get_supabase_client")
def test_delete_template_as_owner(mock_get_client):
    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    with patch("services.template_store.get_template") as mock_get:
        mock_get.return_value = {"id": "t1", "created_by": "user1", "is_admin_only": False, "is_public": True}
        mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value.data = [{"id": "t1"}]

        result = template_store.delete_template("user1", "t1", is_admin=False)
        assert result is True


@patch("services.template_store.get_supabase_client")
def test_delete_template_not_owner(mock_get_client):
    with patch("services.template_store.get_template") as mock_get:
        mock_get.return_value = {"id": "t1", "created_by": "other", "is_admin_only": False, "is_public": True}

        result = template_store.delete_template("user1", "t1", is_admin=False)
        assert result is False
