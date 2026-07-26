"""Shared line/bullet statistics for the content & writing checks.

Pure string helpers with no PDF/DOCX awareness, so the same checks run on
whichever extraction the router considers best for the format. Note that
DOCX native list bullets are paragraph styling, not text — python-docx
yields only the paragraph text, so literal markers are all we can see.
"""

import re

# Bullet markers as they survive text extraction (•, -, *, en dash, ▪),
# plus LaTeX \item remnants from broken conversions.
BULLET_MARKER_RE = re.compile(r"^(?:[•\-*–▪]|\\item\b)\s*")

_LEADING_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")

# One regex per recognizable date style; two or more styles in the same
# resume reads as inconsistent formatting.
DATE_STYLE_RES = {
    "Mon YYYY": re.compile(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b",
        re.IGNORECASE,
    ),
    "MM/YYYY": re.compile(r"\b(?:0?[1-9]|1[0-2])/\d{4}\b"),
    "YYYY-MM": re.compile(r"\b(?:19|20)\d{2}-(?:0[1-9]|1[0-2])\b"),
}

# A URL split by a line break: the token run ends at the newline and text
# continues immediately on the next line.
URL_LINEBREAK_RE = re.compile(r"https?://\S*\n\S")
# A URL with an extraction gap after a dot ("https://linkedin. com/…").
URL_GAP_RE = re.compile(
    r"https?://\S*\.\s+(?:com|org|net|io|co|dev|me|in)\b", re.IGNORECASE
)


def lines(text):
    """Non-empty, stripped lines in document order."""
    return [stripped for line in text.splitlines() if (stripped := line.strip())]


def bullet_lines(text):
    """Bullet lines with their marker stripped, in document order."""
    found = []
    for line in lines(text):
        match = BULLET_MARKER_RE.match(line)
        if match and line[match.end() :]:
            found.append(line[match.end() :])
    return found


def leading_word(line):
    """First alphabetic word of a line, or None."""
    match = _LEADING_WORD_RE.search(line)
    return match.group(0) if match else None
