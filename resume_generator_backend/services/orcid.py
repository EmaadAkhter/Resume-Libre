import json
import logging
import re

import httpx

from services.cache import get_redis

logger = logging.getLogger("resume_libre")

# Bare iD or any orcid.org URL — the checksum char may be a (case-insensitive) X.
ORCID_ID_RE = re.compile(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", re.IGNORECASE)


def _extract_orcid_id(raw: str) -> str:
    match = ORCID_ID_RE.search(raw or "")
    return match.group(0).upper() if match else ""


def _dig(data, *keys):
    """Walk nested dicts/lists, returning None as soon as a step is missing.

    ORCID records are deeply nested and any level may be None.
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        elif isinstance(data, list) and isinstance(key, int):
            data = data[key] if 0 <= key < len(data) else None
        else:
            return None
    return data


async def fetch_orcid_profile(orcid_id: str) -> dict:
    orcid_id = _extract_orcid_id(orcid_id)
    if not orcid_id:
        return {}

    try:
        redis = get_redis()
        cached = await redis.get(f"orcid:{orcid_id}")
        if cached:
            return json.loads(cached)
    except Exception:
        redis = None

    data = await _fetch_from_orcid(orcid_id)
    if data and redis:
        try:
            await redis.setex(f"orcid:{orcid_id}", 86400, json.dumps(data))  # 24h TTL
        except Exception:
            pass
    return data


async def _fetch_from_orcid(orcid_id: str) -> dict:
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
    headers = {"Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url, headers=headers)

        if response.status_code != 200:
            logger.warning(f"ORCID record fetch failed: {response.status_code}")
            return {}
        return _extract_profile(response.json())
    except Exception as e:
        logger.warning(f"ORCID fetch error: {e}")
        return {}


def _extract_profile(record: dict) -> dict:
    given = _dig(record, "person", "name", "given-names", "value")
    family = _dig(record, "person", "name", "family-name", "value")
    name = " ".join(part for part in (given, family) if part)

    employments = []
    groups = _dig(record, "activities-summary", "employments", "affiliation-group")
    for group in groups or []:
        summary = _dig(group, "summaries", 0, "employment-summary")
        org = _dig(summary, "organization", "name")
        role = _dig(summary, "role-title")
        if not org and not role:
            continue
        employments.append(
            {
                "org": org or "",
                "role": role or "",
                "start": _dig(summary, "start-date", "year", "value") or "",
                "end": _dig(summary, "end-date", "year", "value") or "Present",
            }
        )
        if len(employments) >= 5:
            break

    educations = []
    groups = _dig(record, "activities-summary", "educations", "affiliation-group")
    for group in groups or []:
        summary = _dig(group, "summaries", 0, "education-summary")
        org = _dig(summary, "organization", "name")
        degree = _dig(summary, "role-title")
        if not org and not degree:
            continue
        educations.append(
            {
                "org": org or "",
                "degree": degree or "",
                "year": _dig(summary, "end-date", "year", "value") or "",
            }
        )
        if len(educations) >= 3:
            break

    works = []
    seen_titles = set()
    for group in _dig(record, "activities-summary", "works", "group") or []:
        summary = _dig(group, "work-summary", 0)
        title = _dig(summary, "title", "title", "value")
        if not title or title.strip().lower() in seen_titles:
            continue
        seen_titles.add(title.strip().lower())
        works.append(
            {
                "title": title,
                "year": _dig(summary, "publication-date", "year", "value") or "",
            }
        )
        if len(works) >= 15:
            break

    # No name, no works, no employments — nothing worth a prompt section.
    if not name and not works and not employments:
        return {}

    profile: dict = {}
    if name:
        profile["name"] = name
    if employments:
        profile["employments"] = employments
    if educations:
        profile["educations"] = educations
    if works:
        profile["works"] = works
    return profile
