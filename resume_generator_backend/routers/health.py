from fastapi import APIRouter, HTTPException

from services.genrate_resume import load_system_prompt
from schemas.export import SystemPromptResponse

router = APIRouter(tags=["health"])


@router.get("/")
async def root():
    return {
        "message": "Resume-Libre API",
        "version": "2.1.0",
        "endpoints": {
            "/health": "GET - Health check",
            "/get-system-prompt": "GET - Get system prompt",
            "/generate-resume": "POST - Generate resume",
            "/generate-resume-stream": "GET - Stream resume generation (SSE)",
            "/export-resume": "POST - Export resume",
            "/extract-resume": "POST - Extract text from file",
            "/resumes": "CRUD - Resume management",
            "/resumes/{id}/versions": "Version history",
            "/resumes/{id}/branches": "Branch management",
            "/resumes/{id}/tags": "Tag management",
            "/templates": "CRUD - Template management",
            "/debug/events": "GET - Live event stream (SSE)",
        },
    }


@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-libre"}


@router.get("/get-system-prompt", response_model=SystemPromptResponse)
async def get_system_prompt():
    try:
        prompt = load_system_prompt()
        return SystemPromptResponse(prompt=prompt, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load system prompt: {str(e)}")
