import os
from typing import Optional
from openai import OpenAI
from fastapi import HTTPException

from .clean_up import validate_and_fix_format, validate_resume_quality
from .events import bus


def load_system_prompt() -> str:
    from pathlib import Path

    current_dir = Path(__file__).parent
    prompt_path = current_dir.parent / "system_promt.txt"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"system_promt.txt not found at {prompt_path}")


SYSTEM_PROMPT = load_system_prompt()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )


def _get_model() -> str:
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
    return model


async def generate_resume_content(
    user_prompt: str, custom_system_prompt: Optional[str] = None, template_format: str = "md"
) -> str:
    """Generate a resume via OpenRouter.

    Args:
        user_prompt: The assembled user prompt with GitHub data + additional info.
        custom_system_prompt: Optional override for the system prompt.
        template_format: 'md' or 'tex' — determines output format instruction.
    """
    system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT

    if template_format == "tex":
        system_prompt += "\n\nIMPORTANT: Output the resume in LaTeX format, not Markdown."
    else:
        system_prompt += "\n\nOutput the resume in Markdown format."

    client = _get_client()
    model = _get_model()

    try:
        completion = client.chat.completions.create(
            model=model,
            max_tokens=8000,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"reasoning": {"enabled": True}},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    resume = completion.choices[0].message.content

    if not resume or len(resume.strip()) < 100:
        raise HTTPException(status_code=500, detail="Generated resume is too short or empty")

    resume = validate_and_fix_format(resume)

    validation = validate_resume_quality(resume)

    if validation["warnings"]:
        print("Resume warnings:", validation["warnings"])

    if not validation["valid"]:
        error_msg = "Generated resume has critical issues: " + "; ".join(validation["issues"])
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    words = len(resume.split())
    lines = validation["line_count"]
    print(f"Generated resume: {words} words, {lines} content lines")

    return resume.strip()


async def generate_resume_stream(
    user_prompt: str, custom_system_prompt: Optional[str] = None, template_format: str = "md"
):
    """Stream resume generation token by token via OpenRouter.

    Yields individual token strings as they arrive.
    """
    system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT

    if template_format == "tex":
        system_prompt += "\n\nIMPORTANT: Output the resume in LaTeX format, not Markdown."
    else:
        system_prompt += "\n\nOutput the resume in Markdown format."

    client = _get_client()
    model = _get_model()

    try:
        stream = client.chat.completions.create(
            model=model,
            max_tokens=8000,
            temperature=0.1,
            stream=True,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"reasoning": {"enabled": True}},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    full_content = ""

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            token = chunk.choices[0].delta.content
            full_content += token
            yield token

    if len(full_content.strip()) < 100:
        raise HTTPException(status_code=500, detail="Generated resume is too short or empty")
