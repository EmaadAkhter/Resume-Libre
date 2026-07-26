"""Deterministic parseability checks. Each check returns a dict:
{id, status: "pass"|"warn"|"fail", reason, fix, category, confidence: "high"}.

`category` is one of extraction/layout/typography/contact/content/file and
drives the grouped report client-side. Explicitly no blended numeric score —
a checklist is honest, a score is not.
"""

import difflib
import re

# Canonical contact/section regexes live in ats.extraction so the checklist
# and the field-extraction preview can never disagree.
from ats import textstats
from ats.extraction import (
    EMAIL_RE as _EMAIL_RE,
)
from ats.extraction import (
    HEADER_RE as _HEADER_RE,
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
    ALL_CAPS_MAX_LINES,
    BULLET_DENSITY_WARN,
    COMPLETENESS_PASS,
    FILE_SIZE_WARN_MB,
    GLUED_DENSITY_RATIO,
    HYPHEN_BREAK_MAX,
    LENGTH_MAX_WORDS,
    LENGTH_MIN_WORDS,
    LONG_BULLET_WORDS,
    MAX_FONT_NAMES,
    MIN_SECTION_HEADERS,
    PAGE_FAIL_COUNT,
    PAGE_WARN_COUNT,
    QUANTIFIED_BULLETS_INFO,
    REPEATED_VERB_COUNT,
    TINY_FONT_WARN_FRACTION,
)

# Private Use Areas (BMP + planes 15/16): where icon fonts live.
_PUA_RANGES = ((0xE000, 0xF8FF), (0xF0000, 0xFFFFD), (0x100000, 0x10FFFD))

# Decorative codepoints that ATS parsers mangle: emoji/pictographs,
# misc symbols + dingbats, and box-drawing lines. Distinct from
# encoding_sanity, which covers U+FFFD and Private Use Areas.
_SPECIAL_RANGES = (
    (0x1F300, 0x1FAFF),  # emoji & pictographs
    (0x2600, 0x27BF),  # misc symbols + dingbats
    (0x2500, 0x257F),  # box drawing
)


def _check(check_id, status, reason, fix, category, metric=None):
    result = {
        "id": check_id,
        "status": status,
        "reason": reason,
        "fix": fix,
        "category": category,
        "confidence": "high",
    }
    if metric is not None:
        result["metric"] = metric
    return result


def _info(check_id, reason, fix, category, metric=None):
    """Informational suggestion: status "info", excluded from summary counts."""
    check = _check(check_id, "info", reason, fix, category, metric=metric)
    check["informational"] = True
    return check


def _normalize(text):
    return " ".join(text.lower().split())


_SNIPPET_MAX_CHARS = 60


def _snippet(line):
    stripped = line.strip()
    if len(stripped) > _SNIPPET_MAX_CHARS:
        stripped = stripped[:_SNIPPET_MAX_CHARS].rstrip() + "…"
    return f'"{stripped}"'


def scanned_pdf():
    return _check(
        "scanned-pdf",
        "fail",
        "Almost no text could be extracted — this PDF appears to be a scan or "
        "photo, which most ATS software cannot read at all.",
        "Export a text-based PDF from your editor, not a scan/photo.",
        category="extraction",
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
    metric = {
        "kind": "ratio",
        "value": ratio,
        "warn_below": AGREEMENT_PASS,
        "fail_below": AGREEMENT_WARN,
    }
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
            category="extraction",
            metric=metric,
        )
    return _check(
        "extraction-agreement",
        status,
        f"Two independent PDF text extractors agree with ratio {ratio:.2f} "
        "(1.00 = identical). Low agreement means ATS parsers will each read "
        "your resume differently.",
        "Simplify the layout — avoid text boxes, overlapping elements, and "
        "unusual fonts so every parser reads the same text.",
        category="extraction",
        metric=metric,
    )


def extraction_agreement_single(fmt):
    return _check(
        "extraction-agreement",
        "pass",
        f"{fmt} files have a single, well-defined text stream; the "
        "cross-extractor agreement check does not apply.",
        "No action needed.",
        category="extraction",
    )


def columns(column_count):
    if column_count <= 1:
        return _check(
            "columns",
            "pass",
            "Single-column layout — text extracts in the order it is read.",
            "No action needed.",
            category="layout",
        )
    return _check(
        "columns",
        "warn",
        f"Detected {column_count} columns; many ATS read left-to-right across "
        "columns, scrambling the order of your content.",
        "Use a single-column layout so sections stay in reading order.",
        category="layout",
    )


def tables(table_count):
    if table_count == 0:
        return _check(
            "tables",
            "pass",
            "No tables detected.",
            "No action needed.",
            category="layout",
        )
    return _check(
        "tables",
        "warn",
        f"Detected {table_count} table(s); ATS parsers often flatten table "
        "cells out of order or drop them entirely.",
        "Replace tables with plain text lines or simple bullet lists.",
        category="layout",
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
            category="typography",
        )
    return _check(
        "encoding-sanity",
        "fail",
        f"Found {bad} unreadable character(s) (replacement chars or icon-font "
        "glyphs); icon fonts/broken encoding turn into garbage in ATS.",
        "Remove icon fonts (phone/email/location symbols) and re-export with "
        "standard fonts embedded.",
        category="typography",
    )


def content_completeness(text_a, text_b, glued=False):
    set_a = set(_normalize(text_a).split())
    set_b = set(_normalize(text_b).split())
    union = set_a | set_b
    jaccard = len(set_a & set_b) / len(union) if union else 1.0
    metric = {"kind": "ratio", "value": jaccard, "warn_below": COMPLETENESS_PASS}
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
            category="extraction",
            metric=metric,
        )
    return _check(
        "content-completeness",
        status,
        f"Word-set overlap between two independent extractions is {jaccard:.2f} "
        "(1.00 = identical). Missing words mean some content is invisible to "
        "certain parsers.",
        "Check that no text lives in images, headers/footers, or decorative "
        "elements that parsers skip.",
        category="extraction",
        metric=metric,
    )


def content_completeness_single(fmt):
    return _check(
        "content-completeness",
        "pass",
        f"{fmt} files have a single, well-defined text stream; the "
        "cross-extractor completeness check does not apply.",
        "No action needed.",
        category="extraction",
    )


def section_headers(text):
    found = _find_sections(text)
    if len(found) >= MIN_SECTION_HEADERS:
        return _check(
            "section-headers",
            "pass",
            f"Found standard section headers: {', '.join(found)}.",
            "No action needed.",
            category="content",
        )
    return _check(
        "section-headers",
        "warn",
        "Fewer than two standard section headers (Experience, Education, "
        "Skills, Projects, Summary, Certifications — or common synonyms) "
        "were found; standard section names help ATS categorize your content.",
        "Rename custom headings to conventional ones like 'Experience' and "
        "'Education'.",
        category="content",
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
            category="contact",
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
            category="contact",
        )
    return _check(
        "contact-info",
        "fail",
        "Neither an email address nor a phone number was found in the extracted text.",
        "Add plain-text contact details near the top (not inside an image, "
        "header graphic, or icon font).",
        category="contact",
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
            category="contact",
        )
    return _check(
        "link-only-contact",
        "warn",
        f"These contact details exist only as clickable link annotations, "
        f"not as visible text: {', '.join(link_only)}.",
        "Spell the URL out as visible text — many ATS only read text, not "
        "link annotations.",
        category="contact",
    )


def header_footer_contact(in_margins):
    if in_margins:
        return _check(
            "header-footer-contact",
            "fail",
            "Contact info lives in the page header/footer — many parsers "
            "skip those regions.",
            "Move email/phone into the document body, near the top of page 1.",
            category="layout",
        )
    return _check(
        "header-footer-contact",
        "pass",
        "Contact info is in the document body, not the page margins.",
        "No action needed.",
        category="layout",
    )


def page_count(n):
    metric = {"kind": "count", "value": n}
    if n < PAGE_WARN_COUNT:
        return _check(
            "page-count",
            "pass",
            "Single page — the format recruiters and parsers expect.",
            "No action needed.",
            category="file",
            metric=metric,
        )
    if n < PAGE_FAIL_COUNT:
        return _check(
            "page-count",
            "warn",
            f"{n} pages. Two pages are acceptable for senior or academic "
            "profiles, but most screeners only read page one closely.",
            "Cut to one page unless your seniority or field genuinely needs "
            "two — keep the strongest content on page one.",
            category="file",
            metric=metric,
        )
    return _check(
        "page-count",
        "fail",
        f"{n} pages — resumes this long get skimmed at best; many reviewers "
        "and some parsers stop after the first pages.",
        "Cut to one page (two at most for senior/academic profiles) by "
        "removing older or less relevant items.",
        category="file",
        metric=metric,
    )


def resume_length(word_count):
    metric = {
        "kind": "band",
        "value": word_count,
        "low": LENGTH_MIN_WORDS,
        "high": LENGTH_MAX_WORDS,
        "unit": "words",
    }
    if word_count < LENGTH_MIN_WORDS:
        return _check(
            "resume-length",
            "warn",
            f"Only {word_count} words extracted — too sparse; parsers and "
            "recruiters see a thin document with little to match against.",
            f"Flesh out experience and project bullets until you reach "
            f"roughly {LENGTH_MIN_WORDS}–{LENGTH_MAX_WORDS} words.",
            category="content",
            metric=metric,
        )
    if word_count > LENGTH_MAX_WORDS:
        return _check(
            "resume-length",
            "warn",
            f"{word_count} words extracted — this reads as bloat or keyword "
            "stuffing, and both parsers and recruiters lose the signal.",
            f"Trim to roughly {LENGTH_MIN_WORDS}–{LENGTH_MAX_WORDS} words by "
            "cutting weak bullets and redundant keywords.",
            category="content",
            metric=metric,
        )
    return _check(
        "resume-length",
        "pass",
        f"{word_count} words extracted — within the "
        f"{LENGTH_MIN_WORDS}–{LENGTH_MAX_WORDS} word range that reads well "
        "for both parsers and recruiters.",
        "No action needed.",
        category="content",
        metric=metric,
    )


def font_count(fonts):
    names = sorted(fonts)
    if len(names) <= MAX_FONT_NAMES:
        return _check(
            "font-count",
            "pass",
            f"{len(names)} embedded font(s) — a restrained, consistent set.",
            "No action needed.",
            category="typography",
        )
    sample = ", ".join(names[:5])
    return _check(
        "font-count",
        "warn",
        f"{len(names)} embedded fonts ({sample}, …) — font soup harms text "
        "extraction and looks noisy to human readers.",
        f"Stick to at most {MAX_FONT_NAMES} fonts — one family plus its "
        "bold/italic variants is plenty.",
        category="typography",
    )


def tiny_font(fraction):
    metric = {
        "kind": "ratio",
        "value": fraction,
        "warn_above": TINY_FONT_WARN_FRACTION,
    }
    if fraction < TINY_FONT_WARN_FRACTION:
        return _check(
            "tiny-font",
            "pass",
            "Body text stays at readable sizes; no significant fine print.",
            "No action needed.",
            category="typography",
            metric=metric,
        )
    return _check(
        "tiny-font",
        "warn",
        f"{fraction:.0%} of the text is set below 8.5pt — fine print gets "
        "dropped or misread by parsers, and humans skip it too.",
        "Raise body text to 10pt or larger; if content only fits at tiny "
        "sizes, cut content instead.",
        category="typography",
        metric=metric,
    )


def images(count):
    if count == 0:
        return _check(
            "images",
            "pass",
            "No embedded images — everything on the page is real text.",
            "No action needed.",
            category="layout",
        )
    return _check(
        "images",
        "warn",
        f"{count} embedded image(s). Photos and graphics are invisible to "
        "ATS text extraction, some parsers choke on them, and photos invite "
        "bias screening in many markets.",
        "Remove photos, logos, and graphics; express any content they "
        "carried as plain text.",
        category="layout",
    )


def special_characters(text):
    seen = [ch for ch in text if any(lo <= ord(ch) <= hi for lo, hi in _SPECIAL_RANGES)]
    if not seen:
        return _check(
            "special-characters",
            "pass",
            "No emoji, dingbats, or box-drawing characters in the extracted text.",
            "No action needed.",
            category="typography",
        )
    sample = " ".join(list(dict.fromkeys(seen))[:5])
    return _check(
        "special-characters",
        "warn",
        f"Found {len(seen)} decorative character(s) such as {sample} — emoji "
        "and box-drawing glyphs turn into garbage or noise in many ATS "
        "parsers.",
        "Replace emoji and drawn lines/boxes with plain text (use '-' for "
        "bullets and section rules).",
        category="typography",
    )


def margins(edge_text):
    if not edge_text:
        return _check(
            "margins",
            "pass",
            "All text keeps a safe distance from the page edges.",
            "No action needed.",
            category="layout",
        )
    return _check(
        "margins",
        "warn",
        "Text sits at the very edge of the page — print-scan pipelines and "
        "some viewers crop edge content, so it can vanish before parsing.",
        "Keep at least a 1.5cm (0.6in) margin on every side of the page.",
        category="layout",
    )


_WEAK_PHRASES = (
    "worked on",
    "helped with",
    "assisted in",
    "responsible for",
    "tasked with",
)
_MAX_SNIPPETS = 3


def writing_tips(text):
    """Informational-only writing suggestions; None when nothing matched.

    Never counted as a failure: status is "info" and the dict carries
    informational=True, which report.build_report excludes from the summary.
    """
    snippets = []
    for line in text.splitlines():
        if any(phrase in line.lower() for phrase in _WEAK_PHRASES):
            snippets.append(_snippet(line))
            if len(snippets) == _MAX_SNIPPETS:
                break
    if not snippets:
        return None
    return _info(
        "writing-tips",
        "Some lines lead with passive phrasing that undersells your work: "
        f"{'; '.join(snippets)}.",
        "Start bullets with power verbs like developed, implemented, "
        "designed, optimized, built, led, automated, reduced, increased.",
        category="content",
    )


# ── content & writing (text-based, all formats) ──────────────────────


def bullet_density(text):
    all_lines = textstats.lines(text)
    if not all_lines:
        return _check(
            "bullet-density",
            "pass",
            "No text lines to measure — no bullets detected.",
            "No action needed.",
            category="content",
        )
    ratio = len(textstats.bullet_lines(text)) / len(all_lines)
    metric = {"kind": "ratio", "value": ratio, "warn_below": BULLET_DENSITY_WARN}
    if ratio >= BULLET_DENSITY_WARN:
        return _check(
            "bullet-density",
            "pass",
            f"{ratio:.0%} of lines are bullet points — experience reads as "
            "scannable bullets, not prose.",
            "No action needed.",
            category="content",
            metric=metric,
        )
    return _check(
        "bullet-density",
        "warn",
        f"Only {ratio:.0%} of lines are bullet points — walls of prose don't "
        "scan; recruiters skim, and parsers lose the structure.",
        "Convert experience into bullet points — one achievement per line, "
        "starting with an action verb.",
        category="content",
        metric=metric,
    )


_MIN_BULLETS_FOR_QUANTIFIED = 3


def quantified_bullets(text):
    """Informational nudge toward numbers in bullets; None when too few
    bullets exist for the fraction to mean anything."""
    bullets = textstats.bullet_lines(text)
    if len(bullets) < _MIN_BULLETS_FOR_QUANTIFIED:
        return None
    quantified = [
        b for b in bullets if "%" in b or "$" in b or any(ch.isdigit() for ch in b)
    ]
    ratio = len(quantified) / len(bullets)
    metric = {"kind": "ratio", "value": ratio, "warn_below": QUANTIFIED_BULLETS_INFO}
    if ratio >= QUANTIFIED_BULLETS_INFO:
        return _check(
            "quantified-bullets",
            "pass",
            f"{len(quantified)} of {len(bullets)} bullets carry a number — "
            "quantified impact is what screeners scan for.",
            "No action needed.",
            category="content",
            metric=metric,
        )
    unquantified = [b for b in bullets if b not in quantified][:2]
    samples = "; ".join(_snippet(b) for b in unquantified)
    return _info(
        "quantified-bullets",
        f"Only {len(quantified)} of {len(bullets)} bullets contain a number, "
        f"e.g. {samples}.",
        "Add numbers: scope, %, users, ms — 'Cut build time 40%' lands harder "
        "than 'Improved build time'.",
        category="content",
        metric=metric,
    )


def long_bullets(text):
    over = [
        b for b in textstats.bullet_lines(text) if len(b.split()) > LONG_BULLET_WORDS
    ]
    if not over:
        return _check(
            "long-bullets",
            "pass",
            f"No bullet runs past {LONG_BULLET_WORDS} words.",
            "No action needed.",
            category="content",
        )
    worst = max(over, key=lambda b: len(b.split()))
    return _info(
        "long-bullets",
        f"{len(over)} bullet(s) run past {LONG_BULLET_WORDS} words — the "
        f"longest: {_snippet(worst)}. Long bullets bury the achievement.",
        "Split rambling bullets — one achievement each, at most two lines.",
        category="content",
    )


def repeated_verbs(text):
    counts = {}
    for bullet in textstats.bullet_lines(text):
        word = textstats.leading_word(bullet)
        if word:
            entry = counts.setdefault(word.casefold(), [word, 0])
            entry[1] += 1
    repeated = [entry for entry in counts.values() if entry[1] >= REPEATED_VERB_COUNT]
    if not repeated:
        return _check(
            "repeated-verbs",
            "pass",
            "No action verb opens three or more bullets — good variety.",
            "No action needed.",
            category="content",
        )
    word, count = max(repeated, key=lambda entry: entry[1])
    return _info(
        "repeated-verbs",
        f'"{word}" starts {count} bullets — vary your action verbs so each line lands.',
        "Rotate strong verbs: built, led, designed, shipped, automated, cut, scaled.",
        category="content",
    )


# Standalone I (case-sensitive), excluding I/O, I.T., I-9 style tokens;
# me/my with word boundaries (\b keeps MySQL and Medium from matching).
_FIRST_PERSON_I_RE = re.compile(r"\bI\b(?![/.+&-])")
_FIRST_PERSON_ME_MY_RE = re.compile(r"\b(?:me|my)\b", re.IGNORECASE)


def first_person(text):
    count = len(_FIRST_PERSON_I_RE.findall(text)) + len(
        _FIRST_PERSON_ME_MY_RE.findall(text)
    )
    if count == 0:
        return _check(
            "first-person",
            "pass",
            "No first-person pronouns — the implied-first-person convention "
            "is respected.",
            "No action needed.",
            category="content",
        )
    return _check(
        "first-person",
        "warn",
        f"Found {count} first-person pronoun(s) (I, me, my) — resumes are "
        "written in implied first person, and pronouns waste keyword space.",
        "Drop I/me/my and start each bullet directly with the action verb.",
        category="content",
    )


_BUZZWORDS = (
    "team player",
    "hard-working",
    "hardworking",
    "results-driven",
    "go-getter",
    "synergy",
    "passionate",
    "detail-oriented",
    "think outside the box",
    "self-starter",
    "dynamic",
    "proactive",
)
_BUZZWORD_RES = tuple(
    re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE) for phrase in _BUZZWORDS
)


def buzzwords(text):
    hits = [
        phrase
        for phrase, pattern in zip(_BUZZWORDS, _BUZZWORD_RES)
        if pattern.search(text)
    ]
    if not hits:
        return _check(
            "buzzwords",
            "pass",
            "No cliché filler phrases detected.",
            "No action needed.",
            category="content",
        )
    return _info(
        "buzzwords",
        f"Found cliché phrase(s): {', '.join(hits)} — empty adjectives every "
        "screener has read a thousand times.",
        "Replace clichés with evidence: a shipped project, a number, a concrete skill.",
        category="content",
    )


def all_caps_lines(text):
    shouting = [
        line
        for line in textstats.lines(text)
        if sum(ch.isalpha() for ch in line) >= 3
        and line.isupper()
        and not _HEADER_RE.match(line)
    ]
    if len(shouting) <= ALL_CAPS_MAX_LINES:
        return _check(
            "all-caps-lines",
            "pass",
            "Body text is not set in ALL CAPS.",
            "No action needed.",
            category="content",
        )
    return _check(
        "all-caps-lines",
        "warn",
        f"{len(shouting)} lines are set in ALL CAPS (e.g. "
        f"{_snippet(shouting[0])}) — hard to read, and some parsers mistake "
        "caps lines for section headings.",
        "Reserve capitals for short section headings; set body lines in sentence case.",
        category="content",
    )


def duplicate_bullets(text):
    seen = {}
    for bullet in textstats.bullet_lines(text):
        key = " ".join(bullet.lower().split())
        entry = seen.setdefault(key, [bullet, 0])
        entry[1] += 1
    duplicated = [entry for entry in seen.values() if entry[1] >= 2]
    if not duplicated:
        return _check(
            "duplicate-bullets",
            "pass",
            "No bullet appears twice.",
            "No action needed.",
            category="content",
        )
    bullet, count = max(duplicated, key=lambda entry: entry[1])
    return _check(
        "duplicate-bullets",
        "warn",
        f"The same bullet appears {count} times: {_snippet(bullet)} — "
        "duplicated lines read as filler to screeners.",
        "Delete repeated bullets; make each line a distinct achievement.",
        category="content",
    )


def date_format_consistency(text):
    styles = [
        name
        for name, pattern in textstats.DATE_STYLE_RES.items()
        if pattern.search(text)
    ]
    if len(styles) < 2:
        return _check(
            "date-format-consistency",
            "pass",
            "Dates use a single consistent style.",
            "No action needed.",
            category="content",
        )
    return _check(
        "date-format-consistency",
        "warn",
        f"Mixed date styles found: {' and '.join(styles)} — inconsistent "
        "dates make parsed work history look sloppy or misaligned.",
        "Pick one date format everywhere, e.g. 'Jan 2023 – Present'.",
        category="content",
    )


_HYPHEN_BREAK_RE = re.compile(r"[a-z]-\n[a-z]")


def hyphenation_breaks(text):
    count = len(_HYPHEN_BREAK_RE.findall(text))
    if count <= HYPHEN_BREAK_MAX:
        return _check(
            "hyphenation-breaks",
            "pass",
            "No significant end-of-line word hyphenation.",
            "No action needed.",
            category="content",
        )
    return _check(
        "hyphenation-breaks",
        "warn",
        f"{count} words are split across lines with hyphens (typical of "
        "justified text) — parsers index the broken halves as garbage tokens.",
        "Left-align text and disable automatic hyphenation before exporting.",
        category="content",
    )


def _heading_line(line):
    """The line when it is a bare section heading (only the header synonym
    plus trailing punctuation), else None."""
    match = _HEADER_RE.match(line)
    if match and not line[match.end() :].strip(" \t:–—-"):
        return line
    return None


def orphan_headings(text):
    all_lines = textstats.lines(text)
    orphans = []
    for index, line in enumerate(all_lines):
        if _heading_line(line) is None:
            continue
        following = all_lines[index + 1] if index + 1 < len(all_lines) else None
        if following is None or _heading_line(following):
            orphans.append(line)
    if not orphans:
        return _check(
            "orphan-headings",
            "pass",
            "Every section heading is followed by content.",
            "No action needed.",
            category="content",
        )
    if len(orphans) == 1:
        named = f"Section heading {_snippet(orphans[0])} has no content under it"
    else:
        named = (
            f"Section heading {_snippet(orphans[0])} and {len(orphans) - 1} "
            "more have no content under them"
        )
    return _check(
        "orphan-headings",
        "warn",
        f"{named} — empty sections make the resume parse as incomplete.",
        "Fill the section with content or remove its heading.",
        category="content",
    )


# ── contact (text-based, all formats) ────────────────────────────────


def multiple_emails(text):
    emails = list(
        dict.fromkeys(match.group(0).lower() for match in _EMAIL_RE.finditer(text))
    )
    if len(emails) <= 1:
        return _check(
            "multiple-emails",
            "pass",
            "No conflicting email addresses — at most one found.",
            "No action needed.",
            category="contact",
        )
    return _check(
        "multiple-emails",
        "warn",
        f"An ATS takes the first email it finds, and this resume has "
        f"{len(emails)} (found: {', '.join(emails)}).",
        "Keep exactly one professional email — remove stale addresses.",
        category="contact",
    )


def broken_links(text):
    wrapped = bool(textstats.URL_LINEBREAK_RE.search(text))
    gapped = bool(textstats.URL_GAP_RE.search(text))
    if not (wrapped or gapped):
        return _check(
            "broken-links",
            "pass",
            "No URLs are split across lines or broken by stray spaces.",
            "No action needed.",
            category="contact",
        )
    return _check(
        "broken-links",
        "warn",
        "A URL is split across a line break or contains a gap — the pieces "
        "index as separate, dead tokens in an ATS.",
        "Keep each URL on a single line, or shorten the visible text "
        "(e.g. linkedin.com/in/name).",
        category="contact",
    )


# ── file ─────────────────────────────────────────────────────────────


def file_size(byte_len):
    size_mb = round(byte_len / (1024 * 1024), 2)
    metric = {
        "kind": "band",
        "value": size_mb,
        "low": 0,
        "high": FILE_SIZE_WARN_MB,
        "unit": "MB",
    }
    if byte_len <= FILE_SIZE_WARN_MB * 1024 * 1024:
        return _check(
            "file-size",
            "pass",
            f"{size_mb} MB — under the {FILE_SIZE_WARN_MB} MB cap common on "
            "ATS upload portals.",
            "No action needed.",
            category="file",
            metric=metric,
        )
    return _check(
        "file-size",
        "warn",
        f"{size_mb} MB — many ATS portals cap uploads at {FILE_SIZE_WARN_MB} "
        "MB, and heavy resumes usually mean embedded photos or scans.",
        "Compress or re-export the file; remove photos and high-resolution graphics.",
        category="file",
        metric=metric,
    )


def encrypted_pdf(is_encrypted):
    if not is_encrypted:
        return _check(
            "encrypted-pdf",
            "pass",
            "No encryption or password protection on the file.",
            "No action needed.",
            category="file",
        )
    return _check(
        "encrypted-pdf",
        "fail",
        "This PDF is password- or permission-protected — many ATS parsers "
        "cannot open protected files at all, and the application is dropped.",
        "Re-export the PDF without a password or printing/copying restrictions.",
        category="file",
    )


# Working-file tokens with custom boundaries: filenames use _ and - as
# separators, which \b would treat as word-internal.
_MESSY_FILENAME_RES = (
    re.compile(r"(?<![a-z0-9])(?:untitled|final|copy)(?![a-z0-9])", re.IGNORECASE),
    re.compile(r"\(\d+\)"),
)


def filename_check(filename):
    name = (filename or "").strip()
    messy = (
        name in ("resume.pdf", "resume.docx")
        or " " in name
        or any(pattern.search(name) for pattern in _MESSY_FILENAME_RES)
    )
    if not messy:
        return _check(
            "filename",
            "pass",
            f'"{name}" is a clean, professional file name.',
            "No action needed.",
            category="file",
        )
    return _info(
        "filename",
        f'"{name}" looks like a working file name — recruiters and ATS '
        "portals show it verbatim.",
        "Name it FirstLast_Role.pdf (no spaces, no 'final', no '(1)').",
        category="file",
    )
