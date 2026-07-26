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

# The editor's auto-check uploads a synthesized blob under this name; the
# filename check would nag about it on every compile, so it is skipped.
_SYNTHESIZED_FILENAME = "resume.pdf"


def _text_checks(text):
    """Format-independent content & contact checks on the best extracted
    text, shared by the PDF and DOCX branches. Checks that decline to run
    (writing_tips, quantified_bullets) return None and are dropped."""
    candidates = [
        checks.bullet_density(text),
        checks.quantified_bullets(text),
        checks.long_bullets(text),
        checks.repeated_verbs(text),
        checks.first_person(text),
        checks.buzzwords(text),
        checks.all_caps_lines(text),
        checks.duplicate_bullets(text),
        checks.date_format_consistency(text),
        checks.hyphenation_breaks(text),
        checks.orphan_headings(text),
        checks.writing_tips(text),
        checks.multiple_emails(text),
        checks.broken_links(text),
    ]
    return [check for check in candidates if check is not None]


@router.get("/roles")
async def list_roles():
    """Role presets usable as a job-description substitute in /analyze-ats."""
    from ats.skills import ROLE_KEYWORDS

    return {"roles": sorted(ROLE_KEYWORDS)}


@router.post("/check")
@limiter.limit(
    "30/hour"
)  # pure CPU; generous so the editor's auto-check per compile fits
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
            stats = extractors.pdf_stats(data)
            glued = checks.detect_glued(plumber_text, fitz_text)
            links = extractors.extract_pdf_links(data)
            extracted = extraction.extract_fields_rules(plumber_text, links=links)
            results = [
                checks.extraction_agreement(plumber_text, fitz_text, glued=glued),
                checks.columns(layout_info["max_columns"]),
                checks.tables(layout_info["table_count"]),
                checks.encoding_sanity(plumber_text + fitz_text),
                checks.content_completeness(plumber_text, fitz_text, glued=glued),
                checks.section_headers(plumber_text),
                checks.contact_info(plumber_text),
                checks.page_count(stats["page_count"]),
                # max of both extractions — glued-word extractions undercount
                checks.resume_length(
                    max(len(plumber_text.split()), len(fitz_text.split()))
                ),
                checks.font_count(stats["font_names"]),
                checks.tiny_font(stats["tiny_char_fraction"]),
                checks.images(stats["image_count"]),
                checks.special_characters(plumber_text + fitz_text),
                checks.margins(stats["edge_text"]),
                checks.link_only_contact(extracted),
                checks.header_footer_contact(layout.contact_in_margins(data)),
                checks.encrypted_pdf(stats["is_encrypted"]),
                checks.file_size(len(data)),
            ]
            best_text = plumber_text
        else:
            # ponytail: DOCX layout inspection is shallow — python-docx sees
            # tables but not multi-column section formatting. Upgrade path:
            # parse w:cols in the document XML.
            # DOCX has no link annotations or page margins to inspect, so
            # the link-only-contact and header-footer-contact checks are
            # PDF-only.
            text, table_count = extractors.extract_docx(data)
            extracted = extraction.extract_fields_rules(text)
            results = [
                checks.extraction_agreement_single("DOCX"),
                checks.columns(1),
                checks.tables(table_count),
                checks.encoding_sanity(text),
                checks.content_completeness_single("DOCX"),
                checks.section_headers(text),
                checks.contact_info(text),
                checks.resume_length(len(text.split())),
                checks.file_size(len(data)),
            ]
            best_text = text
        if file.filename != _SYNTHESIZED_FILENAME:
            results.append(checks.filename_check(file.filename))
        results.extend(_text_checks(best_text))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not parse this file — it may be corrupted or "
            "password-protected.",
        )

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

    links = None
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
            # Same link-annotation fallback as /ats/check, so the AI resolve
            # pass never erases a link-recovered contact field client-side.
            links = extractors.extract_pdf_links(data)
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

    rules = extraction.extract_fields_rules(text, links=links)
    resolved = await resolve_low_confidence(text, rules, demo=user.get("demo", False))
    return {
        "filename": file.filename,
        "extracted": {field: result.model_dump() for field, result in resolved.items()},
    }
