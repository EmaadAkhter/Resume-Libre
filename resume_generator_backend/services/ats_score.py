"""ATS keyword score: compare a resume against a job description via LLM.

Returns a structured match report (percent, matched/missing keywords,
summary) instead of free text, so the frontend can render it directly.
"""

import logging
import time
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from services.genrate_resume import _get_client, _get_model
from services.llm_json import extract_json

logger = logging.getLogger("resume_libre")

MAX_RESUME_CHARS = 12_000
MAX_JD_CHARS = 8_000

SYSTEM_PROMPT = (
    "You are an ATS keyword analyst. Compare the resume against the job "
    "description (or the expected keywords for the stated target role). "
    "Return ONLY a JSON object with keys: match_percent "
    "(integer 0-100), matched_keywords (array of strings), missing_keywords "
    "(array of {keyword, importance: high|medium|low, suggestion}), summary "
    "(string, <=500 chars). The resume may be LaTeX source; analyze only its "
    "textual content. Never invent resume content."
)

RETRY_MESSAGE = (
    "Your previous reply was not valid JSON matching the schema. "
    "Reply with ONLY the JSON object."
)


class KeywordGap(BaseModel):
    keyword: str
    importance: Literal["high", "medium", "low"]
    suggestion: str


class AtsScoreResult(BaseModel):
    match_percent: int = Field(ge=0, le=100)
    matched_keywords: list[str]
    missing_keywords: list[KeywordGap]
    summary: str = Field(max_length=500)


# Canned result for demo mode — no API keys, no LLM cost.
DEMO_RESULT = AtsScoreResult(
    match_percent=78,
    matched_keywords=["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs"],
    missing_keywords=[
        KeywordGap(
            keyword="Kubernetes",
            importance="high",
            suggestion="Mention container orchestration experience, e.g. "
            "deployments or services you managed.",
        ),
        KeywordGap(
            keyword="GraphQL",
            importance="medium",
            suggestion="Add GraphQL if you have used it alongside REST APIs.",
        ),
        KeywordGap(
            keyword="Terraform",
            importance="low",
            suggestion="List any infrastructure-as-code tools you have used.",
        ),
    ],
    summary=(
        "Strong overlap on core backend skills. Adding container "
        "orchestration and API schema keywords would lift the match further."
    ),
)


def _call_llm(client, model: str, messages: list[dict]):
    """One completion call. Try JSON mode first; some OpenRouter models
    reject response_format, so retry once without it before giving up."""
    try:
        return client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except Exception:
        return client.chat.completions.create(
            model=model,
            temperature=0.1,
            max_tokens=2000,
            messages=messages,
        )


async def analyze_ats(
    resume_text: str,
    job_description: str | None = None,
    target_role: str | None = None,
    demo: bool = False,
) -> AtsScoreResult:
    """Score resume keyword match via OpenRouter, against either a pasted
    job description or a named target role (preset keyword list)."""
    if demo:
        return DEMO_RESULT

    resume_text = resume_text[:MAX_RESUME_CHARS]

    if job_description:
        basis = f"JOB DESCRIPTION:\n{job_description[:MAX_JD_CHARS]}"
    else:
        from ats.skills import ROLE_KEYWORDS

        keywords = ROLE_KEYWORDS.get(target_role or "")
        if keywords is None:
            raise HTTPException(
                status_code=422,
                detail=f"Unknown target role. Valid roles: {sorted(ROLE_KEYWORDS)}",
            )
        basis = (
            f"TARGET ROLE: {target_role}\n"
            f"EXPECTED KEYWORDS FOR THIS ROLE:\n{', '.join(keywords)}"
        )

    client = _get_client()
    model = _get_model()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"RESUME:\n{resume_text}\n\n{basis}",
        },
    ]

    started = time.monotonic()
    for _attempt in range(2):
        try:
            completion = _call_llm(client, model, messages)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ATS analysis failed: {e!s}")

        raw = completion.choices[0].message.content or ""
        try:
            result = AtsScoreResult.model_validate(extract_json(raw))
        except (ValidationError, ValueError):
            # Malformed reply — retry once with an explicit correction.
            messages = [
                *messages,
                {"role": "assistant", "content": raw},
                {"role": "user", "content": RETRY_MESSAGE},
            ]
            continue

        usage = getattr(completion, "usage", None)
        logger.info(
            "ats_score model=%s duration=%.1fs prompt_tokens=%s completion_tokens=%s",
            model,
            time.monotonic() - started,
            getattr(usage, "prompt_tokens", None),
            getattr(usage, "completion_tokens", None),
        )
        return result

    raise HTTPException(
        status_code=502,
        detail="ATS analysis produced unreadable output — try again",
    )
