"""LLM fallback field resolution (stage 3 part 2).

Rules-based extraction (ats.extraction) tags each field with a confidence.
This module takes the fields the rules could not resolve confidently and
asks the LLM — twice, at different temperatures — to extract just those.
Two agreeing samples earn "medium" confidence; disagreement is surfaced
honestly via llm_disagreement instead of silently picking a winner.

High-confidence rules results are never touched, and a dead LLM never
breaks the endpoint: total failure returns the rules results unchanged.
"""

import logging

from pydantic import BaseModel, EmailStr, Field, ValidationError, field_validator

from ats.extraction import (
    _PHONE_DIGITS_MAX,
    _PHONE_DIGITS_MIN,
    DATE_RE,
    FieldResult,
)
from services.genrate_resume import _get_client, _get_model
from services.llm_json import extract_json

logger = logging.getLogger("resume_libre")

MAX_TEXT_CHARS = 6_000
_TEMPERATURES = (0.3, 0.5)

SYSTEM_PROMPT_TEMPLATE = (
    "Extract ONLY the requested fields from this resume text. "
    "Return ONLY a JSON object with keys: {fields}. "
    "Use null when a field is absent. Never guess or invent."
)


class LLMExtractedFields(BaseModel):
    """Per-field validation schema for LLM replies.

    Built one field at a time (per-field try/except) so one hallucinated
    field never discards the rest of an otherwise usable sample.
    """

    name: str | None = Field(None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = None
    job_title: str | None = Field(None, max_length=100)
    company: str | None = Field(None, max_length=100)
    dates: list[str] | None = None

    @field_validator("phone")
    @classmethod
    def _phone_digit_count(cls, v):
        if v is None:
            return v
        digits = sum(c.isdigit() for c in v)
        if not _PHONE_DIGITS_MIN <= digits <= _PHONE_DIGITS_MAX:
            raise ValueError(
                f"phone must contain {_PHONE_DIGITS_MIN}-{_PHONE_DIGITS_MAX} digits"
            )
        return v

    @field_validator("dates")
    @classmethod
    def _dates_look_like_dates(cls, v):
        if v is None:
            return v
        for item in v:
            if not DATE_RE.fullmatch(item.strip()):
                raise ValueError(f"not a recognizable date range: {item!r}")
        return v


# Fields the LLM schema can express; anything else (linkedin, sections, …)
# stays whatever the rules said.
_RESOLVABLE = frozenset(LLMExtractedFields.model_fields)

# Canned resolution for demo mode — no API keys, no LLM cost.
DEMO_RESOLUTION = {
    "name": FieldResult(value="Jane Doe", confidence="medium", method="llm"),
    "email": FieldResult(
        value="jane.doe@example.com", confidence="medium", method="llm"
    ),
    "phone": FieldResult(value="+1 555 123 4567", confidence="medium", method="llm"),
    "dates": FieldResult(
        value=["Jan 2022 – Present"], confidence="medium", method="llm"
    ),
}

_INVALID = object()  # sentinel: sample missing/unparseable for this field


def _call_llm(client, model: str, messages: list[dict], temperature: float):
    """One completion call. Try JSON mode first; some OpenRouter models
    reject response_format, so retry once without it before giving up."""
    try:
        return client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=1000,
            response_format={"type": "json_object"},
            messages=messages,
        )
    except Exception:
        return client.chat.completions.create(
            model=model,
            temperature=temperature,
            max_tokens=1000,
            messages=messages,
        )


def _sample(client, model: str, messages: list[dict], temperature: float):
    """One full sample: call + JSON recovery. None means the sample is dead."""
    try:
        completion = _call_llm(client, model, messages, temperature)
        raw = completion.choices[0].message.content or ""
        return extract_json(raw)
    except Exception as e:
        logger.warning("llm_fallback sample (temp=%s) failed: %s", temperature, e)
        return None


def _validated(sample, field: str):
    """Validate one field of one sample dict; _INVALID if it fails."""
    if sample is None:
        return _INVALID
    try:
        model = LLMExtractedFields(**{field: sample.get(field)})
    except ValidationError:
        return _INVALID
    return getattr(model, field)


def _norm(value):
    if isinstance(value, str):
        return value.strip().casefold()
    if isinstance(value, list):
        return [_norm(v) for v in value]
    return value


def _merge_field(prior: FieldResult, v1, v2) -> FieldResult:
    """Merge two validated samples for one field against the rules result."""
    if v1 is _INVALID:
        return FieldResult(value=None, confidence="low", method="llm", failed=True)

    # The rules had an actual candidate value and the LLM contradicts it:
    # keep the rules value — the disagreement itself is the signal.
    if prior.value is not None and _norm(v1) != _norm(prior.value):
        return prior.model_copy(update={"confidence": "low", "llm_disagreement": True})

    if v2 is not _INVALID and _norm(v1) == _norm(v2):
        return FieldResult(value=v1, confidence="medium", method="llm")

    return FieldResult(value=v1, confidence="low", method="llm", llm_disagreement=True)


async def resolve_low_confidence(
    text: str, rules: dict[str, FieldResult], demo: bool = False
) -> dict[str, FieldResult]:
    """Resolve failed/low-confidence rules fields via double-sampled LLM calls.

    Returns the full merged field dict. High-confidence rules results are
    never overwritten, and LLM failure degrades to the rules results.
    """
    unresolved = [
        field
        for field, result in rules.items()
        # failed, uncertain, OR absent — a field the regexes never found is
        # exactly what the LLM pass exists to recover (#30).
        if (result.failed or result.confidence != "high" or result.value is None)
        and field in _RESOLVABLE
    ]
    if not unresolved:
        return rules

    if demo:
        return {
            **rules,
            **{f: DEMO_RESOLUTION[f] for f in unresolved if f in DEMO_RESOLUTION},
        }

    client = _get_client()
    model = _get_model()
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_TEMPLATE.format(fields=", ".join(unresolved)),
        },
        {"role": "user", "content": text[:MAX_TEXT_CHARS]},
    ]

    samples = [_sample(client, model, messages, t) for t in _TEMPERATURES]
    if all(s is None for s in samples):
        logger.warning(
            "llm_fallback: both samples failed; returning rules results unchanged"
        )
        return rules

    run1, run2 = samples
    resolved = dict(rules)
    for field in unresolved:
        resolved[field] = _merge_field(
            rules[field], _validated(run1, field), _validated(run2, field)
        )
    return resolved
