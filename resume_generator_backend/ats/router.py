"""ATS endpoints.

POST /ats/check — stateless resume parseability checker. Unauthenticated
by design: it is pure-CPU, top-of-funnel, and rate-limited per IP.

POST /ats/extract — rules extraction plus LLM fallback for the ambiguous
fields. Requires auth (or demo) because it spends LLM tokens.

Uploads are processed entirely in memory and never written to disk
(PII policy, see PRIVACY.md).
"""

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from ats import checks, extraction, extractors, input_handler, layout, report
from ats.llm_fallback import resolve_low_confidence
from core.deps import require_user_or_demo
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
            best_text = plumber_text
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
            best_text = text
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse this file — it may be corrupted or "
            "password-protected.",
        )

    extracted = extraction.extract_fields_rules(best_text)
    return report.build_report(file.filename, results, extracted)


@router.post("/extract")
@limiter.limit("10/hour")
async def extract_fields(
    request: Request,
    file: UploadFile = File(...),
    user: dict = Depends(require_user_or_demo),
):
    data = await file.read()
    kind = input_handler.validate_upload(file.filename, data)

    try:
        if kind == "pdf":
            # Same best-text choice as /ats/check: pdfplumber's extraction.
            text = extractors.extract_pdf_pdfplumber(data)
            if input_handler.is_scanned(text):
                raise HTTPException(
                    status_code=422,
                    detail="This PDF has no extractable text — it looks like a "
                    "scan or photo export. AI field extraction needs real text; "
                    "export a text-based PDF from your editor.",
                )
        else:
            text, _ = extractors.extract_docx(data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse this file — it may be corrupted or "
            "password-protected.",
        )

    rules = extraction.extract_fields_rules(text)
    resolved = await resolve_low_confidence(text, rules, demo=user.get("demo", False))
    return {
        "filename": file.filename,
        "extracted": {field: result.model_dump() for field, result in resolved.items()},
    }
