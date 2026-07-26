from typing import Literal

from pydantic import BaseModel


class ResumeRequest(BaseModel):
    github_username: str | None = None
    linkedin_url: str | None = None
    additional_info: str | None = None
    job_description: str | None = None
    priority: Literal["experience", "projects", "balanced"] = "experience"
    custom_system_prompt: str | None = None
    resume_template: str | None = None
    template_format: Literal["md", "tex"] = "md"


class ResumeResponse(BaseModel):
    resume: str
    status: str = "success"


class CreateResumeRequest(BaseModel):
    name: str
    template_id: str | None = None


class CommitVersionRequest(BaseModel):
    content: str
    branch_name: str = "main"
    message: str = ""
    latex_content: str | None = None
    generation_prompt: str | None = None
    template_id: str | None = None


class CreateBranchRequest(BaseModel):
    name: str
    from_version_id: str | None = None


class MergeBranchRequest(BaseModel):
    source_branch: str
    target_branch: str = "main"


class CreateTagRequest(BaseModel):
    name: str
    version_id: str
