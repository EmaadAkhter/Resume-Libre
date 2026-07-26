"""POST /ats/check — stateless resume parseability checker.

Unauthenticated by design: it is pure-CPU, top-of-funnel, and rate-limited
per IP. The upload is processed entirely in memory and never written to
disk (PII policy, see PRIVACY.md).
"""

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from ats import checks, extractors, input_handler, layout, report
from core.limiter import limiter

router = APIRouter(prefix="/ats", tags=["ats"])


@router.post("/check")
@limiter.limit("5/hour")
async def check_resume(request: Request, file: UploadFile = File(...)):
    data = await file.read()
    kind = input_handler.validate_upload(file.filename, data)

    try:
        if kind == "pdf":
            plumber_text = extractors.extract_pdf_pdfplumber(data)
            if input_handler.is_scanned(plumber_text):
                return report.build_report(file.filename, [checks.scanned_pdf()])
            fitz_text = extractors.extract_pdf_pymupdf(data)
            layout_info = layout.analyze(data)
            results = [
                checks.extraction_agreement(plumber_text, fitz_text),
                checks.columns(layout_info["max_columns"]),
                checks.tables(layout_info["table_count"]),
                checks.encoding_sanity(plumber_text + fitz_text),
                checks.content_completeness(plumber_text, fitz_text),
                checks.section_headers(plumber_text),
                checks.contact_info(plumber_text),
            ]
        else:
            # ponytail: DOCX layout inspection is shallow — python-docx sees
            # tables but not multi-column section formatting. Upgrade path:
            # parse w:cols in the document XML.
            text, table_count = extractors.extract_docx(data)
            results = [
                checks.extraction_agreement_single("DOCX"),
                checks.columns(1),
                checks.tables(table_count),
                checks.encoding_sanity(text),
                checks.content_completeness_single("DOCX"),
                checks.section_headers(text),
                checks.contact_info(text),
            ]
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse this file — it may be corrupted or "
            "password-protected.",
        )

    return report.build_report(file.filename, results)
