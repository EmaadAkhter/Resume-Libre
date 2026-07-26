from typing import Literal

from pydantic import BaseModel


class CreateTemplateRequest(BaseModel):
    name: str
    content: str
    format: Literal["md", "tex"] = "md"
    description: str = ""
    is_admin_only: bool = False
    is_public: bool = True


class UpdateTemplateRequest(BaseModel):
    name: str | None = None
    content: str | None = None
    format: Literal["md", "tex"] | None = None
    description: str | None = None
    is_admin_only: bool | None = None
    is_public: bool | None = None
