from pydantic import BaseModel
from typing import Optional, Literal


class ResumeRequest(BaseModel):
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None
    additional_info: Optional[str] = None
    job_description: Optional[str] = None
    priority: Literal["experience", "projects"] = "experience"
    custom_system_prompt: Optional[str] = None
    resume_template: Optional[str] = None
    template_format: Literal["md", "tex"] = "md"


class ResumeResponse(BaseModel):
    resume: str
    status: str = "success"


class CreateResumeRequest(BaseModel):
    name: str
    template_id: Optional[str] = None


class CommitVersionRequest(BaseModel):
    content: str
    branch_name: str = "main"
    message: str = ""
    latex_content: Optional[str] = None
    generation_prompt: Optional[str] = None
    template_id: Optional[str] = None


class CreateBranchRequest(BaseModel):
    name: str
    from_version_id: Optional[str] = None


class MergeBranchRequest(BaseModel):
    source_branch: str
    target_branch: str = "main"


class CreateTagRequest(BaseModel):
    name: str
    version_id: str
