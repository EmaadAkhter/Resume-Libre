"""Deterministic parseability checks. Each check returns a dict:
{id, status: "pass"|"warn"|"fail", reason, fix, confidence: "high"}.

Explicitly no blended numeric score — a checklist is honest, a score is not.
"""

import difflib

# Canonical contact/section regexes live in ats.extraction so the checklist
# and the field-extraction preview can never disagree.
from ats.extraction import (
    EMAIL_RE as _EMAIL_RE,
)
from ats.extraction import (
    PHONE_CANDIDATE_RE as _PHONE_CANDIDATE_RE,
)
from ats.extraction import (
    find_sections as _find_sections,
)
from ats.thresholds import (
    AGREEMENT_PASS,
    AGREEMENT_WARN,
    COMPLETENESS_PASS,
    GLUED_DENSITY_RATIO,
    MIN_SECTION_HEADERS,
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


def _word_space_density(text):
    """Words per non-space character — near-zero when spaces are missing."""
    normalized = _normalize(text)
    chars = len(normalized.replace(" ", ""))
    return len(normalized.split()) / chars if chars else 0.0


def detect_glued(text_a, text_b):
    """True when one extractor sees far fewer word breaks than the other,
    i.e. it reads the same characters as glued-together words. Called by the
    router and passed into extraction_agreement / content_completeness so
    both explain the shared root cause instead of their generic symptoms."""
    density_a = _word_space_density(text_a)
    density_b = _word_space_density(text_b)
    if max(density_a, density_b) == 0:
        return False
    return min(density_a, density_b) < GLUED_DENSITY_RATIO * max(density_a, density_b)


def extraction_agreement(text_a, text_b, glued=False):
    ratio = difflib.SequenceMatcher(
        None, _normalize(text_a), _normalize(text_b)
    ).ratio()
    if ratio >= AGREEMENT_PASS:
        status = "pass"
    elif ratio >= AGREEMENT_WARN:
        status = "warn"
    else:
        status = "fail"
    if glued and status != "pass":
        words_a = len(_normalize(text_a).split())
        words_b = len(_normalize(text_b).split())
        return _check(
            "extraction-agreement",
            status,
            "One extractor reads your text without word spacing — "
            f"{min(words_a, words_b)} words vs {max(words_a, words_b)} words "
            "from the same characters; usually a font/kerning or design-tool "
            "export issue.",
            "Re-export with a standard font and normal word spacing — for "
            "LaTeX prefer pdflatex with standard fonts over XeLaTeX "
            "fontspec fonts; for design tools, rebuild in a word processor.",
        )
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


def content_completeness(text_a, text_b, glued=False):
    set_a = set(_normalize(text_a).split())
    set_b = set(_normalize(text_b).split())
    union = set_a | set_b
    jaccard = len(set_a & set_b) / len(union) if union else 1.0
    status = "pass" if jaccard >= COMPLETENESS_PASS else "warn"
    if glued and status == "warn":
        return _check(
            "content-completeness",
            "warn",
            f"Word-set overlap is low ({jaccard:.2f}) because of the "
            "word-spacing issue above — fix that first.",
            "Re-export with a standard font and normal word spacing — for "
            "LaTeX prefer pdflatex with standard fonts over XeLaTeX "
            "fontspec fonts; for design tools, rebuild in a word processor.",
        )
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
    found = _find_sections(text)
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
        "Skills, Projects, Summary, Certifications — or common synonyms) "
        "were found; standard section names help ATS categorize your content.",
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


# Contact fields the link-annotation fallback in ats.extraction can fill.
_LINKABLE_FIELDS = ("email", "linkedin", "github")


def link_only_contact(fields):
    """Warn when contact info exists only as a PDF link annotation.

    Contract with ats.extraction: email/linkedin/github are method="regex"
    when read from visible text; method="heuristic" on these fields can only
    mean the value was recovered from a link annotation (see
    _fill_from_links), i.e. it is invisible to text-only parsers.
    """
    link_only = [
        field
        for field in _LINKABLE_FIELDS
        if fields[field].method == "heuristic" and fields[field].value is not None
    ]
    if not link_only:
        return _check(
            "link-only-contact",
            "pass",
            "No contact details rely solely on clickable link annotations.",
            "No action needed.",
        )
    return _check(
        "link-only-contact",
        "warn",
        f"These contact details exist only as clickable link annotations, "
        f"not as visible text: {', '.join(link_only)}.",
        "Spell the URL out as visible text — many ATS only read text, not "
        "link annotations.",
    )


def header_footer_contact(in_margins):
    if in_margins:
        return _check(
            "header-footer-contact",
            "fail",
            "Contact info lives in the page header/footer — many parsers "
            "skip those regions.",
            "Move email/phone into the document body, near the top of page 1.",
        )
    return _check(
        "header-footer-contact",
        "pass",
        "Contact info is in the document body, not the page margins.",
        "No action needed.",
    )


_WEAK_PHRASES = (
    "worked on",
    "helped with",
    "assisted in",
    "responsible for",
    "tasked with",
)
_SNIPPET_MAX_CHARS = 60
_MAX_SNIPPETS = 3


def writing_tips(text):
    """Informational-only writing suggestions; None when nothing matched.

    Never counted as a failure: status is "info" and the dict carries
    informational=True, which report.build_report excludes from the summary.
    """
    snippets = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(phrase in stripped.lower() for phrase in _WEAK_PHRASES):
            if len(stripped) > _SNIPPET_MAX_CHARS:
                stripped = stripped[:_SNIPPET_MAX_CHARS].rstrip() + "…"
            snippets.append(f'"{stripped}"')
            if len(snippets) == _MAX_SNIPPETS:
                break
    if not snippets:
        return None
    check = _check(
        "writing-tips",
        "info",
        "Some lines lead with passive phrasing that undersells your work: "
        f"{'; '.join(snippets)}.",
        "Start bullets with power verbs like developed, implemented, "
        "designed, optimized, built, led, automated, reduced, increased.",
    )
    check["informational"] = True
    return check
