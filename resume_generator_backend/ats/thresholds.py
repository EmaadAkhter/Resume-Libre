"""Numeric thresholds for the ATS parseability checks.

These are MVP values derived from the in-repo test fixture set, pending
real calibration against a labeled resume corpus (issue #31). Treat them
as tunable constants, not ground truth.
"""

# Stage 0 — input handling
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB upload cap
SCANNED_MIN_CHARS = 100  # fewer extracted chars than this => scanned/image PDF

# extraction-agreement (difflib.SequenceMatcher ratio, normalized text)
AGREEMENT_PASS = 0.90
AGREEMENT_WARN = 0.75  # below this => fail

# content-completeness (Jaccard similarity of word sets)
COMPLETENESS_PASS = 0.90

# glued-words diagnosis: one extractor sees far fewer word breaks than the
# other for the same characters. Flag when the lower word-space density is
# below this fraction of the higher one.
GLUED_DENSITY_RATIO = 0.6

# section-headers
MIN_SECTION_HEADERS = 2

# layout — column detection
GUTTER_MIN_WIDTH_PT = 18  # horizontal whitespace wider than this splits columns
MIN_COLUMN_WORDS = 10  # a cluster needs this many words to count as a column
HEADER_BAND_FRACTION = 0.15  # ignore the top slice of each page (full-width headers)

# layout — margin-contact detection: the top/bottom page fraction treated as
# the header/footer band that many ATS parsers skip.
MARGIN_BAND_FRACTION = 0.08

# page-count
PAGE_WARN_COUNT = 2  # exactly 2 pages — acceptable for senior/academic profiles
PAGE_FAIL_COUNT = 3  # 3+ pages — too long for almost every screening pipeline

# resume-length (words in the extracted text)
LENGTH_MIN_WORDS = 200  # below => too sparse
LENGTH_MAX_WORDS = 900  # above => bloat / keyword stuffing

# font-count
MAX_FONT_NAMES = 4  # distinct embedded fonts before "font soup"

# tiny-font
TINY_FONT_PT = 8.5  # glyphs smaller than this are fine print
TINY_FONT_WARN_FRACTION = 0.10  # warn when this share of characters is fine print

# margins — a word whose bbox sits closer to a page edge than this fraction
# of the page width/height risks being cropped by print-scan pipelines.
EDGE_PROXIMITY_FRACTION = 0.015

# ── v2 content & writing checks ──────────────────────────────────────

# bullet-density: bullets / non-empty lines below this reads as prose walls
BULLET_DENSITY_WARN = 0.15

# quantified-bullets: fraction of bullets carrying a digit/%/$ below this
# triggers an informational nudge (never a warning — style, not parsing)
QUANTIFIED_BULLETS_INFO = 0.30

# long-bullets: a single bullet running past this many words rambles
LONG_BULLET_WORDS = 30

# repeated-verbs: the same leading word on this many bullets reads monotone
REPEATED_VERB_COUNT = 3

# all-caps-lines: tolerated ALL-CAPS lines that are not section headers
ALL_CAPS_MAX_LINES = 2

# hyphenation-breaks: tolerated end-of-line hyphenated word splits
HYPHEN_BREAK_MAX = 2

# file-size: many ATS upload portals cap resumes at this size
FILE_SIZE_WARN_MB = 2
