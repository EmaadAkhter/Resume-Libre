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

# section-headers
MIN_SECTION_HEADERS = 2

# layout — column detection
GUTTER_MIN_WIDTH_PT = 18  # horizontal whitespace wider than this splits columns
MIN_COLUMN_WORDS = 10  # a cluster needs this many words to count as a column
HEADER_BAND_FRACTION = 0.15  # ignore the top slice of each page (full-width headers)
