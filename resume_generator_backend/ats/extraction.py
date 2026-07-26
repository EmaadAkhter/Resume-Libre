"""Rules-based field extraction: what an ATS would pull out of the resume.

Owns the canonical contact/section regexes (checks.py imports them back so
the checklist and the extraction preview can never disagree). spaCy NER is
deliberately omitted — its model weights blow the memory budget on the 2GB
host — the LLM fallback (stage 3 part 2) is the upgrade path for anything
these rules miss.
"""

import re
from typing import Literal

from pydantic import BaseModel

from ats.skills import extract_skills

# Canonical regexes — moved here from checks.py, which imports them back.
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# ponytail: naive candidate-then-digit-count phone matching; year ranges with
# 9+ digits can false-positive. Upgrade path: the `phonenumbers` library.
PHONE_CANDIDATE_RE = re.compile(r"\+?[\d(][\d\s().-]{7,}\d")
# Section header synonyms → canonical section names. HEADER_RE matches any
# synonym at line start; find_sections() maps hits back to canonical names.
SECTION_SYNONYMS = {
    "experience": [
        "experience",
        "work experience",
        "employment",
        "work history",
        "internship",
    ],
    "education": ["education", "academic", "qualifications"],
    "skills": ["skills", "technical skills", "core competencies", "technologies"],
    "projects": ["projects", "personal projects", "academic projects", "portfolio"],
    "summary": ["summary", "objective", "profile", "about me", "career objective"],
    "certifications": ["certifications", "certificates", "courses", "training"],
}
_SYNONYM_TO_CANONICAL = {
    synonym: canonical
    for canonical, synonyms in SECTION_SYNONYMS.items()
    for synonym in synonyms
}
HEADER_RE = re.compile(
    # Longest synonym first so "work experience" wins over "experience".
    r"^\s*(" + "|".join(sorted(_SYNONYM_TO_CANONICAL, key=len, reverse=True)) + r")\b",
    re.IGNORECASE | re.MULTILINE,
)


def find_sections(text: str) -> list[str]:
    """Canonical section names found in the text, deduped and sorted."""
    return sorted(
        {_SYNONYM_TO_CANONICAL[m.group(1).lower()] for m in HEADER_RE.finditer(text)}
    )


# Looser phone candidate than the checklist's: also catches short digit runs
# labeled as a phone so we can flag them as malformed instead of missing.
_PHONE_LOOSE_RE = re.compile(
    r"(?:phone|tel|mobile|cell)\D{0,3}(\+?[\d(][\d\s().-]*\d)", re.IGNORECASE
)

LINKEDIN_RE = re.compile(r"linkedin\.com/in/[A-Za-z0-9_%-]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"github\.com/[A-Za-z0-9-]+", re.IGNORECASE)

_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
_DASH = r"\s*[–—-]\s*"  # en dash, em dash, hyphen
DATE_RE = re.compile(
    rf"{_MONTH}\s+\d{{4}}{_DASH}(?:{_MONTH}\s+\d{{4}}|Present)"
    rf"|\b\d{{4}}{_DASH}(?:\d{{4}}|Present)\b"
    rf"|\b(?:0?[1-9]|1[0-2])/\d{{4}}\b",
    re.IGNORECASE,
)

_URL_RE = re.compile(r"https?://|www\.|linkedin\.com|github\.com", re.IGNORECASE)

_PHONE_DIGITS_MIN = 9
_PHONE_DIGITS_MAX = 15
_NAME_SCAN_LINES = 5


class FieldResult(BaseModel):
    value: str | list[str] | None = None
    confidence: Literal["high", "medium", "low"] = "high"
    method: Literal["regex", "heuristic", "llm"] = "regex"
    failed: bool = False
    llm_disagreement: bool = False


def _phone_sane(candidate):
    return _PHONE_DIGITS_MIN <= sum(c.isdigit() for c in candidate) <= _PHONE_DIGITS_MAX


def _extract_phone(text):
    for match in PHONE_CANDIDATE_RE.finditer(text):
        if _phone_sane(match.group(0)):
            return FieldResult(value=match.group(0).strip())
    # No sane candidate — was there a labeled-but-malformed one?
    for match in _PHONE_LOOSE_RE.finditer(text):
        if not _phone_sane(match.group(1)):
            return FieldResult(value=None, failed=True)
    if PHONE_CANDIDATE_RE.search(text):
        # Candidates existed but every one failed the digit-count sanity check.
        return FieldResult(value=None, failed=True)
    return FieldResult(value=None)


def _is_name_line(line):
    tokens = line.split()
    if not 2 <= len(tokens) <= 4:
        return None
    if any(ch.isdigit() for ch in line):
        return None
    title_cased = sum(1 for t in tokens if t.istitle())
    if title_cased * 2 < len(tokens):  # fewer than half title-case
        return None
    return "strict" if title_cased == len(tokens) else "loose"


def _extract_name(text):
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:_NAME_SCAN_LINES]:
        if (
            EMAIL_RE.search(line)
            or PHONE_CANDIDATE_RE.search(line)
            or _URL_RE.search(line)
            or DATE_RE.search(line)
        ):
            continue
        match = _is_name_line(line)
        if match:
            return FieldResult(
                value=line,
                method="heuristic",
                confidence="high" if match == "strict" else "low",
            )
    return FieldResult(value=None, method="heuristic", confidence="low")


def _extract_regex(pattern, text):
    match = pattern.search(text)
    return FieldResult(value=match.group(0) if match else None)


def _extract_dates(text):
    found = [m.group(0) for m in DATE_RE.finditer(text)]
    return FieldResult(value=found or None)


def _extract_sections(text):
    found = find_sections(text)
    return FieldResult(value=found or None)


def _extract_skills(text):
    found = extract_skills(text)
    return FieldResult(value=found or None)


# Which link URI marks which contact field. Contract with checks.py: these
# three fields are otherwise always method="regex", so method="heuristic" on
# email/linkedin/github can only mean "recovered from a link annotation" —
# the link-only-contact check keys off exactly that.
_LINK_FIELD_MARKERS = {
    "linkedin": "linkedin.com/in/",
    "github": "github.com/",
    "email": "mailto:",
}


def _fill_from_links(fields, links):
    for field, marker in _LINK_FIELD_MARKERS.items():
        result = fields[field]
        if result.value is not None or result.failed:
            continue
        for uri in links:
            index = uri.lower().find(marker)
            if index == -1:
                continue
            # For mailto: links the address itself is the value.
            value = uri[index + len(marker) :] if field == "email" else uri
            fields[field] = FieldResult(
                value=value, method="heuristic", confidence="low"
            )
            break


def extract_fields_rules(
    text: str, links: list[str] | None = None
) -> dict[str, FieldResult]:
    """Extract resume fields with regexes and heuristics only (no ML).

    `links` are PDF link-annotation URIs; contact fields invisible in the
    text but present as annotations are filled from them at low confidence.
    """
    fields = {
        "email": _extract_regex(EMAIL_RE, text),
        "phone": _extract_phone(text),
        "linkedin": _extract_regex(LINKEDIN_RE, text),
        "github": _extract_regex(GITHUB_RE, text),
        "name": _extract_name(text),
        "dates": _extract_dates(text),
        "sections": _extract_sections(text),
        "skills": _extract_skills(text),
    }
    if links:
        _fill_from_links(fields, links)
    return fields
