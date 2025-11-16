from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
from Utils.prompt import build_user_prompt
from Utils.fetch_readme import fetch_github_readme
from Utils.genrate_resume import generate_resume_content, load_system_prompt
from Utils.export_utils import markdown_to_pdf, markdown_to_docx, get_filename_base
import io
import pypdf
import docx

load_dotenv()

app = FastAPI(title="Resume Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ResumeRequest(BaseModel):
    github_username: Optional[str] = None
    additional_info: Optional[str] = None
    priority: Literal["experience", "projects"] = "experience"
    custom_system_prompt: Optional[str] = None
    resume_template: Optional[str] = None


class ResumeResponse(BaseModel):
    resume: str
    status: str = "success"


class SystemPromptResponse(BaseModel):
    prompt: str
    status: str = "success"


class ExportRequest(BaseModel):
    markdown_content: str
    format: Literal["pdf", "docx", "md"] = "pdf"


@app.get("/")
async def root():
    return {
        "message": "Resume Generator API",
        "version": "1.0.0",
        "endpoints": {
            "/generate-resume": "POST - Generate one-page resume",
            "/export-resume": "POST - Export resume to PDF/DOCX/MD",
            "/get-system-prompt": "GET - Get current system prompt",
            "/extract-resume": "POST - Extract text from uploaded resume",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "resume-generator"
    }


@app.get("/get-system-prompt", response_model=SystemPromptResponse)
async def get_system_prompt():
    try:
        prompt = load_system_prompt()
        return SystemPromptResponse(prompt=prompt, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load system prompt: {str(e)}")


@app.post("/extract-resume")
async def extract_resume(file: UploadFile = File(...)):
    try:
        content = await file.read()

        if file.filename.endswith('.pdf'):
            pdf_reader = pypdf.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"

        elif file.filename.endswith('.docx'):
            doc = docx.Document(io.BytesIO(content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file.filename.endswith(('.txt', '.md')):
            text = content.decode('utf-8')

        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file format. Please upload PDF, DOCX, TXT, or MD files."
            )

        return {
            "text": text.strip(),
            "filename": file.filename,
            "status": "success"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract text: {str(e)}")


@app.post("/generate-resume", response_model=ResumeResponse)
async def create_resume(request: ResumeRequest):

    if not request.github_username and not request.additional_info:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a GitHub username or additional information"
        )

    try:
        readme_content = ""
        if request.github_username:
            readme_content = await fetch_github_readme(request.github_username)

        user_prompt = build_user_prompt(
            request.github_username or "",
            readme_content,
            request.additional_info or "",
            request.priority,
            request.resume_template
        )

        resume = await generate_resume_content(
            user_prompt,
            request.custom_system_prompt
        )

        return ResumeResponse(resume=resume, status="success")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate resume: {str(e)}"
        )


@app.post("/export-resume")
async def export_resume(request: ExportRequest):

    try:
        filename_base = get_filename_base(request.markdown_content)

        if request.format == "pdf":
            pdf_bytes = markdown_to_pdf(request.markdown_content)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.pdf"
                }
            )

        elif request.format == "docx":
            docx_buffer = markdown_to_docx(request.markdown_content)
            return StreamingResponse(
                docx_buffer,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.docx"
                }
            )

        elif request.format == "md":
            return Response(
                content=request.markdown_content.encode('utf-8'),
                media_type="text/markdown",
                headers={
                    "Content-Disposition": f"attachment; filename={filename_base}.md"
                }
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf', 'docx', or 'md'")

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export resume: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Resume Generator API on http://localhost:8000")
    print("📚 API Documentation available at http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)