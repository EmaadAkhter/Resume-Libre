from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ResumeRequest(BaseModel):
    github_username: str | None = None
    linkedin_url: str | None = None
    hf_username: str | None = Field(None, max_length=60)
    orcid_id: str | None = Field(None, max_length=60)
    additional_info: str | None = None
    job_description: str | None = None
    priority: Literal["experience", "projects", "balanced"] = "experience"
    custom_system_prompt: str | None = None
    resume_template: str | None = None
    template_format: Literal["md", "tex"] = "md"
    # Parseability-check findings from the previous compile, fed back into
    # the prompt so the model fixes them on regeneration.
    ats_feedback: str | None = Field(None, max_length=4000)


class AtsScoreRequest(BaseModel):
    resume_text: str = Field(min_length=100, max_length=60_000)
    job_description: str | None = Field(None, min_length=30, max_length=30_000)
    target_role: str | None = Field(None, max_length=60)

    @model_validator(mode="after")
    def _exactly_one_basis(self):
        if bool(self.job_description) == bool(self.target_role):
            raise ValueError("Provide exactly one of job_description or target_role")
        return self


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
