from typing import Optional
from .auth import get_supabase_client


def list_templates(user_id: str, is_admin: bool = False) -> list:
    """List templates visible to the user: public + own + admin-only (if admin)."""
    client = get_supabase_client()

    if is_admin:
        result = client.table("templates").select("*").order("created_at").execute()
    else:
        result = (
            client.table("templates")
            .select("*")
            .or_("is_public.eq.true,and(is_admin_only.eq.false)")
            .order("created_at")
            .execute()
        )

    # Also include user's own private templates
    own_result = (
        client.table("templates")
        .select("*")
        .eq("created_by", user_id)
        .order("created_at")
        .execute()
    )

    # Merge and deduplicate
    seen = set()
    templates = []
    for t in result.data + own_result.data:
        if t["id"] not in seen:
            seen.add(t["id"])
            templates.append(t)

    return templates


def get_template(user_id: str, template_id: str, is_admin: bool = False) -> Optional[dict]:
    client = get_supabase_client()
    result = client.table("templates").select("*").eq("id", template_id).single().execute()

    if not result.data:
        return None

    template = result.data

    # Access check: public non-admin, or owned by user, or user is admin
    if template["is_admin_only"] and not is_admin and template["created_by"] != user_id:
        return None
    if not template["is_public"] and template["created_by"] != user_id and not is_admin:
        return None

    return template


def create_template(
    user_id: str,
    name: str,
    content: str,
    format: str = "md",
    description: str = "",
    is_admin_only: bool = False,
    is_public: bool = True,
) -> dict:
    client = get_supabase_client()

    result = client.table("templates").insert({
        "name": name,
        "description": description,
        "content": content,
        "format": format,
        "is_admin_only": is_admin_only,
        "is_public": is_public,
        "created_by": user_id,
    }).execute()

    return result.data[0]


def update_template(
    user_id: str,
    template_id: str,
    updates: dict,
    is_admin: bool = False,
) -> Optional[dict]:
    client = get_supabase_client()

    existing = get_template(user_id, template_id, is_admin)
    if not existing:
        return None

    if existing["created_by"] != user_id and not is_admin:
        return None

    allowed_fields = {"name", "description", "content", "format", "is_admin_only", "is_public"}
    clean_updates = {k: v for k, v in updates.items() if k in allowed_fields}
    clean_updates["updated_at"] = "now()"

    result = (
        client.table("templates")
        .update(clean_updates)
        .eq("id", template_id)
        .execute()
    )

    return result.data[0] if result.data else None


def delete_template(user_id: str, template_id: str, is_admin: bool = False) -> bool:
    client = get_supabase_client()

    existing = get_template(user_id, template_id, is_admin)
    if not existing:
        return False

    if existing["created_by"] != user_id and not is_admin:
        return False

    result = client.table("templates").delete().eq("id", template_id).execute()
    return len(result.data) > 0
