"""Deterministic parseability checks. Each check returns a dict:
{id, status: "pass"|"warn"|"fail", reason, fix, confidence: "high"}.

Explicitly no blended numeric score — a checklist is honest, a score is not.
"""

import difflib
import re

from ats.thresholds import (
    AGREEMENT_PASS,
    AGREEMENT_WARN,
    COMPLETENESS_PASS,
    MIN_SECTION_HEADERS,
)

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# ponytail: naive candidate-then-digit-count phone matching; year ranges with
# 9+ digits can false-positive. Upgrade path: the `phonenumbers` library.
_PHONE_CANDIDATE_RE = re.compile(r"\+?[\d(][\d\s().-]{7,}\d")
_HEADER_RE = re.compile(
    r"^\s*(experience|education|skills|projects|summary|work history)\b",
    re.IGNORECASE | re.MULTILINE,
)
# Private Use Areas (BMP + planes 15/16): where icon fonts live.
_PUA_RANGES = ((0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD))


def _check(check_id, status, reason, fix):
    return {
        "id": check_id,
        "status": status,
        "reason": reason,
        "fix": fix,
        "confidence": "high",
    }


def _normalize(text):
    return " ".join(text.lower().split())


def scanned_pdf():
    return _check(
        "scanned-pdf",
        "fail",
        "Almost no text could be extracted — this PDF appears to be a scan or "
        "photo, which most ATS software cannot read at all.",
        "Export a text-based PDF from your editor, not a scan/photo.",
    )


def extraction_agreement(text_a, text_b):
    ratio = difflib.SequenceMatcher(
        None, _normalize(text_a), _normalize(text_b)
    ).ratio()
    if ratio >= AGREEMENT_PASS:
        status = "pass"
    elif ratio >= AGREEMENT_WARN:
        status = "warn"
    else:
        status = "fail"
    return _check(
        "extraction-agreement",
        status,
        f"Two independent PDF text extractors agree with ratio {ratio:.2f} "
        "(1.00 = identical). Low agreement means ATS parsers will each read "
        "your resume differently.",
        "Simplify the layout — avoid text boxes, overlapping elements, and "
        "unusual fonts so every parser reads the same text.",
    )


def extraction_agreement_single(fmt):
    return _check(
        "extraction-agreement",
        "pass",
        f"{fmt} files have a single, well-defined text stream; the "
        "cross-extractor agreement check does not apply.",
        "No action needed.",
    )


def columns(column_count):
    if column_count <= 1:
        return _check(
            "columns",
            "pass",
            "Single-column layout — text extracts in the order it is read.",
            "No action needed.",
        )
    return _check(
        "columns",
        "warn",
        f"Detected {column_count} columns; many ATS read left-to-right across "
        "columns, scrambling the order of your content.",
        "Use a single-column layout so sections stay in reading order.",
    )


def tables(table_count):
    if table_count == 0:
        return _check(
            "tables",
            "pass",
            "No tables detected.",
            "No action needed.",
        )
    return _check(
        "tables",
        "warn",
        f"Detected {table_count} table(s); ATS parsers often flatten table "
        "cells out of order or drop them entirely.",
        "Replace tables with plain text lines or simple bullet lists.",
    )


def encoding_sanity(text):
    bad = sum(
        1
        for ch in text
        if ch == "�" or any(lo <= ord(ch) <= hi for lo, hi in _PUA_RANGES)
    )
    if bad == 0:
        return _check(
            "encoding-sanity",
            "pass",
            "No replacement characters or private-use glyphs in the extracted text.",
            "No action needed.",
        )
    return _check(
        "encoding-sanity",
        "fail",
        f"Found {bad} unreadable character(s) (replacement chars or icon-font "
        "glyphs); icon fonts/broken encoding turn into garbage in ATS.",
        "Remove icon fonts (phone/email/location symbols) and re-export with "
        "standard fonts embedded.",
    )


def content_completeness(text_a, text_b):
    set_a = set(_normalize(text_a).split())
    set_b = set(_normalize(text_b).split())
    union = set_a | set_b
    jaccard = len(set_a & set_b) / len(union) if union else 1.0
    status = "pass" if jaccard >= COMPLETENESS_PASS else "warn"
    return _check(
        "content-completeness",
        status,
        f"Word-set overlap between two independent extractions is {jaccard:.2f} "
        "(1.00 = identical). Missing words mean some content is invisible to "
        "certain parsers.",
        "Check that no text lives in images, headers/footers, or decorative "
        "elements that parsers skip.",
    )


def content_completeness_single(fmt):
    return _check(
        "content-completeness",
        "pass",
        f"{fmt} files have a single, well-defined text stream; the "
        "cross-extractor completeness check does not apply.",
        "No action needed.",
    )


def section_headers(text):
    found = sorted({m.group(1).lower() for m in _HEADER_RE.finditer(text)})
    if len(found) >= MIN_SECTION_HEADERS:
        return _check(
            "section-headers",
            "pass",
            f"Found standard section headers: {', '.join(found)}.",
            "No action needed.",
        )
    return _check(
        "section-headers",
        "warn",
        "Fewer than two standard section headers (Experience, Education, "
        "Skills, Projects, Summary) were found; standard section names help "
        "ATS categorize your content.",
        "Rename custom headings to conventional ones like 'Experience' and "
        "'Education'.",
    )


def contact_info(text):
    has_email = bool(_EMAIL_RE.search(text))
    has_phone = any(
        9 <= sum(c.isdigit() for c in m.group(0)) <= 15
        for m in _PHONE_CANDIDATE_RE.finditer(text)
    )
    if has_email and has_phone:
        return _check(
            "contact-info",
            "pass",
            "Both an email address and a phone number were found in the "
            "extracted text.",
            "No action needed.",
        )
    if has_email or has_phone:
        missing = "phone number" if has_email else "email address"
        return _check(
            "contact-info",
            "warn",
            f"No {missing} was found in the extracted text; recruiters may be "
            "unable to reach you if the ATS can't parse it.",
            f"Add a plain-text {missing} near the top (not inside an image or "
            "icon font).",
        )
    return _check(
        "contact-info",
        "fail",
        "Neither an email address nor a phone number was found in the extracted text.",
        "Add plain-text contact details near the top (not inside an image, "
        "header graphic, or icon font).",
    )
