from typing import Literal

from pydantic import BaseModel


class ExportRequest(BaseModel):
    markdown_content: str
    format: Literal["latex", "latex_pdf"] = "latex_pdf"
    latex_content: str | None = None


class SystemPromptResponse(BaseModel):
    prompt: str
    status: str = "success"
