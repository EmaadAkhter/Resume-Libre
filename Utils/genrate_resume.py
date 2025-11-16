import os
import random
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException
from clean_up import *

with open("system_promt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

async def generate_resume_content(user_prompt: str) -> str:

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

    if not any(api_keys):
        raise HTTPException(status_code=500, detail="OpenRouter API key not configured")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=random.choice([k for k in api_keys if k]),
    )

    completion = client.chat.completions.create(
        model=random.choice([m for m in models if m]),
        max_tokens=1200,
        temperature=0.05,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
    )

    resume = completion.choices[0].message.content

    if not resume or len(resume.strip()) < 50:
        raise HTTPException(status_code=500, detail="Generated resume is too short or empty")


    resume = validate_and_fix_format(resume)


    if '<' in resume or 'iconify' in resume.lower():
        raise HTTPException(status_code=500, detail="Generated resume contains HTML or icon codes")

    words = len(resume.split())
    lines = len([l for l in resume.split('\n') if l.strip()])
    print(f"Generated resume: {words} words, {lines} lines")

    return resume.strip()

