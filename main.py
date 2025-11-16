from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
from dotenv import load_dotenv
import os
from openai import OpenAI
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
import re
import random
from Utils.prompt import build_user_prompt
from Utils.fetch_readme import fetch_github_readme

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


class ResumeResponse(BaseModel):
    resume: str
    status: str = "success"

@app.get("/")
async def root():
    return {
        "message": "Resume Generator API",
        "version": "1.0.0",
        "endpoints": {
            "/generate-resume": "POST - Generate one-page resume",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "resume-generator"}


@app.post("/generate-resume", response_model=ResumeResponse)
async def create_resume(request: ResumeRequest):
    if not request.github_username and not request.additional_info:
        raise HTTPException(
            status_code=400,
            detail="Please provide either a GitHub username or additional information"
        )

    readme_content = await fetch_github_readme(request.github_username or "")

    user_prompt = build_user_prompt(
        request.github_username or "",
        readme_content,
        request.additional_info or "",
        request.priority
    )

    resume = await generate_resume_content(user_prompt)

    return ResumeResponse(resume=resume, status="success")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)