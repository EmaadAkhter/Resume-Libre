from pydantic import BaseModel
from typing import Optional, Literal


class ExportRequest(BaseModel):
    markdown_content: str
    format: Literal["pdf", "docx", "md", "latex", "latex_pdf"] = "pdf"
    latex_content: Optional[str] = None


class SystemPromptResponse(BaseModel):
    prompt: str
    status: str = "success"
