"""Shared helper for recovering a JSON object from an LLM reply.

LLMs asked for "ONLY a JSON object" still routinely wrap it in markdown
fences or add prose around it. This strips that noise instead of failing.
"""

import json
import re


def extract_json(raw: str) -> dict:
    """Strip markdown fences, slice from first '{' to last '}', json.loads.

    Raises ValueError if no JSON object can be recovered.
    """
    text = raw.strip()

    # Drop a leading ```/```json fence and a trailing ``` fence, if present.
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
    text = re.sub(r"\s*```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM reply")

    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in LLM reply: {e}") from e

    if not isinstance(parsed, dict):
        # ValueError, not TypeError: callers catch ValueError for "no usable
        # JSON object", and a top-level array is exactly that case.
        raise ValueError("LLM reply JSON is not an object")  # noqa: TRY004

    return parsed
