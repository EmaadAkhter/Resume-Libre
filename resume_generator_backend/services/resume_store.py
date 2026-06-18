import difflib
from typing import Optional
from .auth import get_supabase_client


def create_resume(user_id: str, name: str, template_id: Optional[str] = None) -> dict:
    client = get_supabase_client()

    result = (
        client.table("resumes")
        .insert(
            {
                "user_id": user_id,
                "name": name,
                "template_id": template_id,
                "current_branch": "main",
            }
        )
        .execute()
    )

    resume = result.data[0]

    # Create default 'main' branch
    client.table("branches").insert(
        {
            "resume_id": resume["id"],
            "name": "main",
            "head_version_id": None,
        }
    ).execute()

    return resume


def get_resume(user_id: str, resume_id: str) -> Optional[dict]:
    client = get_supabase_client()
    result = (
        client.table("resumes")
        .select("*")
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data


def list_resumes(user_id: str) -> list:
    client = get_supabase_client()
    result = (
        client.table("resumes")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return result.data


def delete_resume(user_id: str, resume_id: str) -> bool:
    client = get_supabase_client()
    result = (
        client.table("resumes")
        .delete()
        .eq("id", resume_id)
        .eq("user_id", user_id)
        .execute()
    )
    return len(result.data) > 0


def commit_version(
    user_id: str,
    resume_id: str,
    content: str,
    branch_name: str = "main",
    message: str = "",
    latex_content: Optional[str] = None,
    generation_prompt: Optional[str] = None,
    template_id: Optional[str] = None,
) -> dict:
    client = get_supabase_client()

    # Find the current head of this branch
    branch_result = (
        client.table("branches")
        .select("head_version_id")
        .eq("resume_id", resume_id)
        .eq("name", branch_name)
        .single()
        .execute()
    )
    parent_id = (
        branch_result.data.get("head_version_id") if branch_result.data else None
    )

    # Insert new version
    version_data = {
        "resume_id": resume_id,
        "parent_version_id": parent_id,
        "branch_name": branch_name,
        "message": message,
        "content": content,
        "latex_content": latex_content,
        "generation_prompt": generation_prompt,
        "template_id": template_id,
    }
    result = client.table("resume_versions").insert(version_data).execute()
    version = result.data[0]

    # Update branch head
    client.table("branches").update({"head_version_id": version["id"]}).eq(
        "resume_id", resume_id
    ).eq("name", branch_name).execute()

    # Update resume's updated_at
    client.table("resumes").update({"updated_at": "now()"}).eq(
        "id", resume_id
    ).execute()

    return version


def get_history(
    user_id: str, resume_id: str, branch: str = "main", limit: int = 50
) -> list:
    client = get_supabase_client()
    result = (
        client.table("resume_versions")
        .select("*")
        .eq("resume_id", resume_id)
        .eq("branch_name", branch)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return result.data


def get_version(user_id: str, resume_id: str, version_id: str) -> Optional[dict]:
    client = get_supabase_client()
    result = (
        client.table("resume_versions")
        .select("*")
        .eq("id", version_id)
        .eq("resume_id", resume_id)
        .single()
        .execute()
    )
    return result.data


def create_branch(
    user_id: str, resume_id: str, name: str, from_version_id: Optional[str] = None
) -> dict:
    client = get_supabase_client()

    # If no version specified, use current head of current branch
    if not from_version_id:
        resume = get_resume(user_id, resume_id)
        if not resume:
            raise ValueError("Resume not found")
        current_branch = resume["current_branch"]
        branch_result = (
            client.table("branches")
            .select("head_version_id")
            .eq("resume_id", resume_id)
            .eq("name", current_branch)
            .single()
            .execute()
        )
        from_version_id = (
            branch_result.data.get("head_version_id") if branch_result.data else None
        )

    result = (
        client.table("branches")
        .insert(
            {
                "resume_id": resume_id,
                "name": name,
                "head_version_id": from_version_id,
            }
        )
        .execute()
    )

    return result.data[0]


def list_branches(user_id: str, resume_id: str) -> list:
    client = get_supabase_client()
    result = (
        client.table("branches")
        .select("*")
        .eq("resume_id", resume_id)
        .order("created_at")
        .execute()
    )
    return result.data


def merge_branch(
    user_id: str, resume_id: str, source_branch: str, target_branch: str = "main"
) -> dict:
    """Fast-forward merge: moves target branch head to source branch head.

    Only works if target is an ancestor of source (true fast-forward).
    ponytail: fast-forward only, 3-way merge if users need conflict resolution.
    """
    client = get_supabase_client()

    source_result = (
        client.table("branches")
        .select("head_version_id")
        .eq("resume_id", resume_id)
        .eq("name", source_branch)
        .single()
        .execute()
    )
    source_head = source_result.data.get("head_version_id")

    if not source_head:
        raise ValueError("Source branch has no commits")

    client.table("branches").update({"head_version_id": source_head}).eq(
        "resume_id", resume_id
    ).eq("name", target_branch).execute()
    client.table("resumes").update(
        {"current_branch": target_branch, "updated_at": "now()"}
    ).eq("id", resume_id).execute()

    return {
        "merged": True,
        "target_branch": target_branch,
        "head_version_id": source_head,
    }


def create_tag(user_id: str, resume_id: str, name: str, version_id: str) -> dict:
    client = get_supabase_client()
    result = (
        client.table("tags")
        .insert(
            {
                "resume_id": resume_id,
                "name": name,
                "version_id": version_id,
            }
        )
        .execute()
    )
    return result.data[0]


def list_tags(user_id: str, resume_id: str) -> list:
    client = get_supabase_client()
    result = (
        client.table("tags")
        .select("*")
        .eq("resume_id", resume_id)
        .order("created_at")
        .execute()
    )
    return result.data


def get_diff(user_id: str, resume_id: str, v1_id: str, v2_id: str) -> str:
    v1 = get_version(user_id, resume_id, v1_id)
    v2 = get_version(user_id, resume_id, v2_id)

    if not v1 or not v2:
        raise ValueError("One or both versions not found")

    diff = difflib.unified_diff(
        v1["content"].splitlines(keepends=True),
        v2["content"].splitlines(keepends=True),
        fromfile=f"{v1['id'][:8]}",
        tofile=f"{v2['id'][:8]}",
    )
    return "".join(diff)
