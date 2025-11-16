import os
import random
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException
from .clean_up import validate_and_fix_format, validate_resume_quality


def load_system_prompt() -> str:
    current_dir = Path(__file__).parent
    prompt_path = current_dir.parent / "system_promt.txt"

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"system_promt.txt not found at {prompt_path}")


SYSTEM_PROMPT = load_system_prompt()


async def generate_resume_content(user_prompt: str, custom_system_prompt: str = None) -> str:

    api_keys = [
        os.getenv("O_R_API1"),
        os.getenv("O_R_API2"),
        os.getenv("O_R_API3"),
        os.getenv("O_R_API4"),
        os.getenv("O_R_API5"),
        os.getenv("O_R_API6")
    ]

    models = [
        os.getenv('MODEL1'),
        os.getenv('MODEL2'),
        os.getenv('MODEL3'),
        os.getenv('MODEL4'),
        os.getenv('MODEL5'),
        os.getenv('MODEL6')
    ]

    valid_keys = [k for k in api_keys if k]
    valid_models = [m for m in models if m]

    if not valid_keys:
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    if not valid_models:
        raise HTTPException(status_code=500, detail="No models configured")

    system_prompt = custom_system_prompt if custom_system_prompt else SYSTEM_PROMPT

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=random.choice(valid_keys),
    )

    try:
        completion = client.chat.completions.create(
            model=random.choice(valid_models),
            max_tokens=2000,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    resume = completion.choices[0].message.content

    if not resume or len(resume.strip()) < 100:
        raise HTTPException(status_code=500, detail="Generated resume is too short or empty")

    resume = validate_and_fix_format(resume)

    validation = validate_resume_quality(resume)

    if validation['warnings']:
        print("Resume warnings:", validation['warnings'])

    if not validation['valid']:
        error_msg = "Generated resume has critical issues: " + "; ".join(validation['issues'])
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    words = len(resume.split())
    lines = validation['line_count']
    print(f"Generated resume: {words} words, {lines} content lines")

    return resume.strip()