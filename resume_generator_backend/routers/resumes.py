from fastapi import APIRouter, HTTPException, Depends, Query

from core.deps import verify_jwt
from core.event_types import Events
from services.events import bus
from services import resume_store
from schemas.resume import (
    CreateResumeRequest,
    CommitVersionRequest,
    CreateBranchRequest,
    MergeBranchRequest,
    CreateTagRequest,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


# ─── CRUD ────────────────────────────────────────────


@router.post("")
async def create_resume_record(
    user: dict = Depends(verify_jwt), req: CreateResumeRequest = ...
):
    resume = resume_store.create_resume(user["id"], req.name, req.template_id)
    await bus.publish(
        Events.RESUME_CREATED, {"resume_id": resume["id"], "name": req.name}
    )
    return {"resume": resume, "status": "success"}


@router.get("")
async def list_user_resumes(user: dict = Depends(verify_jwt)):
    resumes = resume_store.list_resumes(user["id"])
    return {"resumes": resumes, "status": "success"}


@router.get("/{resume_id}")
async def get_resume_record(resume_id: str, user: dict = Depends(verify_jwt)):
    resume = resume_store.get_resume(user["id"], resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return {"resume": resume, "status": "success"}


@router.delete("/{resume_id}")
async def delete_resume_record(resume_id: str, user: dict = Depends(verify_jwt)):
    deleted = resume_store.delete_resume(user["id"], resume_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")
    await bus.publish(Events.RESUME_DELETED, {"resume_id": resume_id})
    return {"status": "success", "deleted": True}


# ─── Versioning (Git Model) ──────────────────────────


@router.post("/{resume_id}/versions")
async def commit_resume_version(
    resume_id: str, req: CommitVersionRequest, user: dict = Depends(verify_jwt)
):
    version = resume_store.commit_version(
        user["id"],
        resume_id,
        req.content,
        req.branch_name,
        req.message,
        req.latex_content,
        req.generation_prompt,
        req.template_id,
    )
    await bus.publish(
        Events.VERSION_COMMITTED, {"resume_id": resume_id, "version_id": version["id"]}
    )
    return {"version": version, "status": "success"}


@router.get("/{resume_id}/versions")
async def get_resume_history(
    resume_id: str,
    branch: str = "main",
    limit: int = 50,
    user: dict = Depends(verify_jwt),
):
    history = resume_store.get_history(user["id"], resume_id, branch, limit)
    return {"versions": history, "status": "success"}


@router.get("/{resume_id}/diff")
async def get_resume_diff(
    resume_id: str,
    v1: str = Query(..., description="First version ID"),
    v2: str = Query(..., description="Second version ID"),
    user: dict = Depends(verify_jwt),
):
    diff = resume_store.get_diff(user["id"], resume_id, v1, v2)
    return {"diff": diff, "status": "success"}


@router.post("/{resume_id}/branches")
async def create_resume_branch(
    resume_id: str, req: CreateBranchRequest, user: dict = Depends(verify_jwt)
):
    branch = resume_store.create_branch(
        user["id"], resume_id, req.name, req.from_version_id
    )
    await bus.publish(
        Events.BRANCH_CREATED, {"resume_id": resume_id, "branch": req.name}
    )
    return {"branch": branch, "status": "success"}


@router.get("/{resume_id}/branches")
async def list_resume_branches(resume_id: str, user: dict = Depends(verify_jwt)):
    branches = resume_store.list_branches(user["id"], resume_id)
    return {"branches": branches, "status": "success"}


@router.post("/{resume_id}/merge")
async def merge_resume_branch(
    resume_id: str, req: MergeBranchRequest, user: dict = Depends(verify_jwt)
):
    result = resume_store.merge_branch(
        user["id"], resume_id, req.source_branch, req.target_branch
    )
    await bus.publish(
        Events.BRANCH_MERGED,
        {
            "resume_id": resume_id,
            "source": req.source_branch,
            "target": req.target_branch,
        },
    )
    return {"result": result, "status": "success"}


@router.post("/{resume_id}/tags")
async def create_resume_tag(
    resume_id: str, req: CreateTagRequest, user: dict = Depends(verify_jwt)
):
    tag = resume_store.create_tag(user["id"], resume_id, req.name, req.version_id)
    await bus.publish(Events.TAG_CREATED, {"resume_id": resume_id, "tag": req.name})
    return {"tag": tag, "status": "success"}


@router.get("/{resume_id}/tags")
async def list_resume_tags(resume_id: str, user: dict = Depends(verify_jwt)):
    tags = resume_store.list_tags(user["id"], resume_id)
    return {"tags": tags, "status": "success"}
