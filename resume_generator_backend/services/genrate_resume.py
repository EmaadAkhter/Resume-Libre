import os
import re
from typing import Optional
from openai import OpenAI
from fastapi import HTTPException


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
    user_prompt: str,
    custom_system_prompt: Optional[str] = None,
    template_format: str = "md",
) -> str:
    """Generate a resume via OpenRouter.

    Args:
        user_prompt: The assembled user prompt with GitHub data + additional info.
        custom_system_prompt: Optional override for the system prompt.
        template_format: 'md' or 'tex' — determines output format instruction.
    """
    system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT
    system_prompt += (
        "\n\nOUTPUT FORMAT — COMPLETE LaTeX DOCUMENT:\n"
        "Output a complete, compilable LaTeX document starting with \\documentclass.\n"
        "NO markdown, NO code fences, NO explanatory text outside the document.\n"
        "The document body between \\begin{document} and \\end{document} MUST contain the full resume content."
    )

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

    resume = completion.choices[0].message.content or ""

    # Strip code fences if LLM wrapped output
    resume = re.sub(r"^```[a-z]*\n?", "", resume.strip()).rstrip("`").strip()

    if len(resume) < 100:
        raise HTTPException(
            status_code=500, detail="Generated resume is too short or empty"
        )

    # Validate LaTeX body is non-empty
    body_match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}", resume, re.DOTALL
    )
    body = body_match.group(1).strip() if body_match else ""
    if len(body) < 50:
        raise HTTPException(
            status_code=500,
            detail="Generated LaTeX document body is empty — model failed to fill content",
        )

    return resume


async def generate_resume_stream(
    user_prompt: str,
    custom_system_prompt: Optional[str] = None,
    template_format: str = "md",
):
    """Stream resume generation token by token via OpenRouter.

    Yields individual token strings as they arrive.
    """
    system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT
    system_prompt += (
        "\n\nOUTPUT FORMAT — COMPLETE LaTeX DOCUMENT:\n"
        "Output a complete, compilable LaTeX document starting with \\documentclass.\n"
        "NO markdown, NO code fences, NO explanatory text outside the document.\n"
        "The document body between \\begin{document} and \\end{document} MUST contain the full resume content."
    )

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

    full_content = (
        re.sub(r"^```[a-z]*\n?", "", full_content.strip()).rstrip("`").strip()
    )

    if len(full_content) < 100:
        raise HTTPException(
            status_code=500, detail="Generated resume is too short or empty"
        )

    body_match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}", full_content, re.DOTALL
    )
    body = body_match.group(1).strip() if body_match else ""
    if len(body) < 50:
        raise HTTPException(
            status_code=500,
            detail="Generated LaTeX document body is empty — model failed to fill content",
        )
