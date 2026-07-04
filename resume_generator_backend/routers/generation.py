import io
import json

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from typing import Optional

import pypdf
import docx

from core.limiter import limiter
from schemas.resume import ResumeRequest, ResumeResponse
from services.pipeline import pipeline
from core.event_types import Events
from services.events import bus

router = APIRouter(tags=["generation"])


@router.post("/generate-resume", response_model=ResumeResponse)
@limiter.limit("10/hour")
async def create_resume(request: Request, body: ResumeRequest):
    if not body.github_username and not body.additional_info and not body.linkedin_url:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a GitHub username, LinkedIn URL, or additional information",
        )

    try:
        resume = await pipeline.run(
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
        raise HTTPException(
            status_code=500, detail=f"Failed to generate resume: {str(e)}"
        )


@router.get("/generate-resume-stream")
@limiter.limit("10/hour")
async def stream_resume_generation(
    request: Request,
    github_username: Optional[str] = Query(None),
    linkedin_url: Optional[str] = Query(None),
    additional_info: Optional[str] = Query(None),
    job_description: Optional[str] = Query(None),
    priority: str = Query("experience"),
    custom_system_prompt: Optional[str] = Query(None),
    resume_template: Optional[str] = Query(None),
    template_format: str = Query("tex"),
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


@router.post("/extract-resume")
async def extract_resume(file: UploadFile = File(...)):
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
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")
