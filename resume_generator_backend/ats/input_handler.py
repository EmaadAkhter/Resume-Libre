"""Stage 0 — upload validation. Everything operates on in-memory bytes;
the upload is never written to disk (PII policy, see PRIVACY.md)."""

from fastapi import HTTPException

from ats.thresholds import MAX_FILE_BYTES, SCANNED_MIN_CHARS


def validate_upload(filename, data):
    """Return "pdf" or "docx" for an acceptable upload, else raise 400/413.

    Magic bytes are verified so a JPEG renamed to .pdf is rejected instead
    of producing a garbage report.
    """
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        kind = "pdf"
    elif name.endswith(".docx"):
        kind = "docx"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a .pdf or .docx resume.",
        )

    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large — the limit is 5 MB.",
        )

    if kind == "pdf" and not data.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail=(
                "This file is not a valid PDF — it looks like another format "
                "(e.g. an image) renamed to .pdf. Export a real PDF from your editor."
            ),
        )
    if kind == "docx" and not data.startswith(b"PK"):
        raise HTTPException(
            status_code=400,
            detail=(
                "This file is not a valid DOCX — it looks like another format "
                "renamed to .docx. Save it as .docx from your editor."
            ),
        )
    return kind


def is_scanned(extracted_text):
    """A PDF with almost no extractable text is a scan/photo export."""
    return len((extracted_text or "").strip()) < SCANNED_MIN_CHARS
