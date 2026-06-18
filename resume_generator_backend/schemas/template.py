from pydantic import BaseModel
from typing import Optional, Literal


class CreateTemplateRequest(BaseModel):
    name: str
    content: str
    format: Literal["md", "tex"] = "md"
    description: str = ""
    is_admin_only: bool = False
    is_public: bool = True


class UpdateTemplateRequest(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    format: Optional[Literal["md", "tex"]] = None
    description: Optional[str] = None
    is_admin_only: Optional[bool] = None
    is_public: Optional[bool] = None
