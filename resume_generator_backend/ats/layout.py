"""Hand-rolled layout analysis on top of pdfplumber (no ML, no ONNX).

Column detection: word x-intervals are merged into clusters; a persistent
horizontal whitespace gap wider than GUTTER_MIN_WIDTH_PT between clusters
that both hold real text is treated as a column gutter.

# ponytail: heuristic ceiling is clean western-style resumes — full-width
# body lines mask gutters and dense right-aligned dates can fake one.
# Upgrade path: per-line gutter voting, then a real layout model behind
# this same analyze() interface.
"""

import io

import pdfplumber

from ats.extraction import EMAIL_RE, PHONE_CANDIDATE_RE, _phone_sane
from ats.thresholds import (
    GUTTER_MIN_WIDTH_PT,
    HEADER_BAND_FRACTION,
    MARGIN_BAND_FRACTION,
    MIN_COLUMN_WORDS,
)


def _column_count(page):
    words = page.extract_words()
    # Ignore the top band of the page: a full-width name/contact header
    # would otherwise bridge the gutter between body columns.
    cutoff = page.height * HEADER_BAND_FRACTION
    body = [w for w in words if w["top"] >= cutoff]
    if len(body) < 2 * MIN_COLUMN_WORDS:
        return 1

    clusters = []  # [x_start, x_end, word_count]
    for x0, x1 in sorted((w["x0"], w["x1"]) for w in body):
        if clusters and x0 - clusters[-1][1] < GUTTER_MIN_WIDTH_PT:
            clusters[-1][1] = max(clusters[-1][1], x1)
            clusters[-1][2] += 1
        else:
            clusters.append([x0, x1, 1])
    return max(1, sum(1 for c in clusters if c[2] >= MIN_COLUMN_WORDS))


def _has_email(text):
    return bool(EMAIL_RE.search(text))


def _has_phone(text):
    return any(_phone_sane(m.group(0)) for m in PHONE_CANDIDATE_RE.finditer(text))


def contact_in_margins(data):
    """True when email or phone exists only in the header/footer band.

    Words in the top/bottom MARGIN_BAND_FRACTION of any page are margin
    text; everything else is body text. A contact detail that appears in
    the margins but nowhere in the body is invisible to parsers that skip
    header/footer regions.
    """
    margin_words = []
    body_words = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            top_band = page.height * MARGIN_BAND_FRACTION
            bottom_band = page.height * (1 - MARGIN_BAND_FRACTION)
            for word in page.extract_words():
                if word["top"] < top_band or word["bottom"] > bottom_band:
                    margin_words.append(word["text"])
                else:
                    body_words.append(word["text"])
    margin_text = " ".join(margin_words)
    body_text = " ".join(body_words)
    return (_has_email(margin_text) and not _has_email(body_text)) or (
        _has_phone(margin_text) and not _has_phone(body_text)
    )


def analyze(data):
    """Return {"max_columns": int, "table_count": int} across all pages."""
    max_columns = 1
    table_count = 0
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            max_columns = max(max_columns, _column_count(page))
            table_count += len(page.find_tables())
    return {"max_columns": max_columns, "table_count": table_count}
