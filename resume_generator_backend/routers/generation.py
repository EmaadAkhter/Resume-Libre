import io
import json

import docx
import pypdf
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

from core.deps import require_user_or_demo
from core.event_types import Events
from core.limiter import limiter
from schemas.resume import AtsScoreRequest, ResumeRequest, ResumeResponse
from services.ats_score import analyze_ats
from services.events import bus
from services.pipeline import pipeline

router = APIRouter(tags=["generation"])


@router.post("/generate-resume", response_model=ResumeResponse)
@limiter.limit("10/hour")
async def create_resume(
    request: Request,
    body: ResumeRequest,
    user: dict = Depends(require_user_or_demo),
):
    if not body.github_username and not body.additional_info and not body.linkedin_url:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a GitHub username, LinkedIn URL, or additional information",
        )

    try:
        resume = await pipeline.run(
            demo=user.get("demo", False),
            github_username=body.github_username or "",
            linkedin_url=body.linkedin_url or "",
            additional_info=body.additional_info or "",
            job_description=body.job_description or "",
            priority=body.priority,
            custom_system_prompt=body.custom_system_prompt,
            resume_template=body.resume_template,
            template_format=body.template_format,
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
    additional_info: str | None = Query(None),
    job_description: str | None = Query(None),
    priority: str = Query("experience"),
    custom_system_prompt: str | None = Query(None),
    resume_template: str | None = Query(None),
    template_format: str = Query("tex"),
    user: dict = Depends(require_user_or_demo),
):
    """Stream resume generation via Server-Sent Events (SSE).

    Emits: data: {"event": "token", "content": "..."} for each token.
    Final: data: {"event": "done", "content": "..."} with full resume.
    """
    if not github_username and not additional_info and not linkedin_url:
        raise HTTPException(
            status_code=400,
            detail="Provide github_username, linkedin_url, or additional_info",
        )

    async def event_stream():
        full_content = ""
        try:
            async for token in pipeline.run_stream(
                demo=user.get("demo", False),
                github_username=github_username or "",
                linkedin_url=linkedin_url or "",
                additional_info=additional_info or "",
                job_description=job_description or "",
                priority=priority,
                custom_system_prompt=custom_system_prompt,
                resume_template=resume_template,
                template_format=template_format,
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
