from fastapi import APIRouter, HTTPException, Depends

from core.deps import verify_jwt, get_user_role
from core.event_types import Events
from services.events import bus
from services import template_store
from schemas.template import CreateTemplateRequest, UpdateTemplateRequest

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
async def list_templates(user: dict = Depends(verify_jwt)):
    user_with_role = await get_user_role(user)
    templates = template_store.list_templates(user["id"], user_with_role["role"] == "admin")
    return {"templates": templates, "status": "success"}


@router.get("/{template_id}")
async def get_template(template_id: str, user: dict = Depends(verify_jwt)):
    user_with_role = await get_user_role(user)
    template = template_store.get_template(user["id"], template_id, user_with_role["role"] == "admin")
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"template": template, "status": "success"}


@router.post("")
async def create_template(req: CreateTemplateRequest, user: dict = Depends(verify_jwt)):
    user_with_role = await get_user_role(user)
    is_admin = user_with_role["role"] == "admin"

    if req.is_admin_only and not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create admin-only templates")

    template = template_store.create_template(
        user["id"], req.name, req.content, req.format, req.description,
        req.is_admin_only, req.is_public
    )
    await bus.publish(Events.TEMPLATE_UPLOADED, {"template_id": template["id"], "name": req.name})
    return {"template": template, "status": "success"}


@router.put("/{template_id}")
async def update_template(template_id: str, req: UpdateTemplateRequest, user: dict = Depends(verify_jwt)):
    user_with_role = await get_user_role(user)
    is_admin = user_with_role["role"] == "admin"

    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    template = template_store.update_template(user["id"], template_id, updates, is_admin)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or no permission")
    return {"template": template, "status": "success"}


@router.delete("/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(verify_jwt)):
    user_with_role = await get_user_role(user)
    is_admin = user_with_role["role"] == "admin"

    deleted = template_store.delete_template(user["id"], template_id, is_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Template not found or no permission")
    return {"status": "success", "deleted": True}
