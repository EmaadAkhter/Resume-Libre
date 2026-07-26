import io
import json

import docx
import pypdf
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.deps import require_user_or_demo
from core.event_types import Events
from core.limiter import limiter
from schemas.resume import AtsScoreRequest, ProfileRef, ResumeRequest, ResumeResponse
from services.ats_score import analyze_ats
from services.events import bus
from services.pipeline import pipeline

router = APIRouter(tags=["generation"])

MAX_PROFILES = 10


def _normalize_profiles(
    profiles: list[ProfileRef] | None,
    github_username: str | None = None,
    linkedin_url: str | None = None,
    hf_username: str | None = None,
    orcid_id: str | None = None,
) -> list[ProfileRef]:
    """Merge profile rows with the legacy scalar params into one list.

    Scalars are appended as rows when non-blank, duplicates (same type and
    stripped value) collapse, and the result is capped at MAX_PROFILES.
    """
    refs = list(profiles or [])
    for ptype, value in (
        ("github", github_username),
        ("linkedin", linkedin_url),
        ("huggingface", hf_username),
        ("orcid", orcid_id),
    ):
        if value and value.strip():
            refs.append(ProfileRef(type=ptype, value=value.strip()))

    seen: set[tuple[str, str]] = set()
    normalized: list[ProfileRef] = []
    for ref in refs:
        key = (ref.type, ref.value.strip())
        if not key[1] or key in seen:
            continue
        seen.add(key)
        normalized.append(ref)
    return normalized[:MAX_PROFILES]


def _first_github(profiles: list[ProfileRef]) -> str:
    return next((p.value for p in profiles if p.type == "github"), "")


@router.post("/generate-resume", response_model=ResumeResponse)
@limiter.limit("10/hour")
async def create_resume(
    request: Request,
    body: ResumeRequest,
    user: dict = Depends(require_user_or_demo),
):
    normalized = _normalize_profiles(
        body.profiles,
        body.github_username,
        body.linkedin_url,
        body.hf_username,
        body.orcid_id,
    )
    if not normalized and not body.additional_info:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one profile source or additional information",
        )

    try:
        resume = await pipeline.run(
            demo=user.get("demo", False),
            profiles=normalized,
            github_username=_first_github(normalized),
            additional_info=body.additional_info or "",
            job_description=body.job_description or "",
            priority=body.priority,
            custom_system_prompt=body.custom_system_prompt,
            resume_template=body.resume_template,
            template_format=body.template_format,
            ats_feedback=body.ats_feedback,
        )
        await bus.publish(Events.LLM_COMPLETED, {"length": len(resume)})
        return ResumeResponse(resume=resume, status="success")

    except HTTPException:
        raise
    except Exception as e:
        await bus.publish(Events.VALIDATION_FAILED, {"error": str(e)[:200]})
        raise HTTPException(status_code=500, detail=f"Failed to generate resume: {e!s}")


@router.get("/generate-resume-stream")
@limiter.limit("10/hour")
async def stream_resume_generation(
    request: Request,
    github_username: str | None = Query(None),
    linkedin_url: str | None = Query(None),
    hf_username: str | None = Query(None, max_length=60),
    orcid_id: str | None = Query(None, max_length=60),
    profiles: str | None = Query(None, max_length=4000),
    additional_info: str | None = Query(None),
    job_description: str | None = Query(None),
    priority: str = Query("experience"),
    custom_system_prompt: str | None = Query(None),
    resume_template: str | None = Query(None),
    template_format: str = Query("tex"),
    ats_feedback: str | None = Query(None, max_length=4000),
    user: dict = Depends(require_user_or_demo),
):
    """Stream resume generation via Server-Sent Events (SSE).

    Emits: data: {"event": "token", "content": "..."} for each token.
    Final: data: {"event": "done", "content": "..."} with full resume.
    """
    parsed_profiles: list[ProfileRef] = []
    if profiles:
        try:
            raw = json.loads(profiles)
            if not isinstance(raw, list) or len(raw) > MAX_PROFILES:
                raise ValueError("profiles must be a list of at most 10 entries")
            parsed_profiles = [ProfileRef.model_validate(item) for item in raw]
        except ValueError:  # covers JSONDecodeError and pydantic ValidationError
            raise HTTPException(status_code=422, detail="invalid profiles parameter")

    normalized = _normalize_profiles(
        parsed_profiles, github_username, linkedin_url, hf_username, orcid_id
    )
    if not normalized and not additional_info:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one profile source or additional_info",
        )

    async def event_stream():
        full_content = ""
        try:
            async for token in pipeline.run_stream(
                demo=user.get("demo", False),
                profiles=normalized,
                github_username=_first_github(normalized),
                additional_info=additional_info or "",
                job_description=job_description or "",
                priority=priority,
                custom_system_prompt=custom_system_prompt,
                resume_template=resume_template,
                template_format=template_format,
                ats_feedback=ats_feedback,
            ):
                full_content += token
                yield f"data: {json.dumps({'event': 'token', 'content': token})}\n\n"

            await bus.publish(
                Events.LLM_COMPLETED, {"length": len(full_content), "streaming": True}
            )
            yield f"data: {json.dumps({'event': 'done', 'content': full_content})}\n\n"
        except Exception as e:
            await bus.publish(Events.VALIDATION_FAILED, {"error": str(e)[:200]})
            yield f"data: {json.dumps({'event': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/analyze-ats")
@limiter.limit("10/hour")
async def analyze_ats_score(
    request: Request,
    body: AtsScoreRequest,
    user: dict = Depends(require_user_or_demo),
):
    """Score how well a resume matches a job description (ATS keywords)."""
    result = await analyze_ats(
        resume_text=body.resume_text,
        job_description=body.job_description,
        target_role=body.target_role,
        demo=user.get("demo", False),
    )
    return result.model_dump()


@router.post("/extract-resume")
async def extract_resume(
    file: UploadFile = File(...),
    user: dict = Depends(require_user_or_demo),
):
    try:
        content = await file.read()

        if file.filename.endswith(".pdf"):
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        elif file.filename.endswith(".docx"):
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file.filename.endswith((".txt", ".md", ".tex")):
            text = content.decode("utf-8")

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload PDF, DOCX, TXT, MD, or TEX files.",
            )

        return {"text": text.strip(), "filename": file.filename, "status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {e!s}")
