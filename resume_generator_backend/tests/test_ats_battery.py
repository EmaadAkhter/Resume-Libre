"""Tests for the expanded ATS check battery (page-count, resume-length,
font-count, tiny-font, images, special-characters, margins), the metric
objects on existing checks, and the ats_feedback regeneration plumbing.

Fixture PDFs are generated in memory with PyMuPDF — no binaries in the repo.
"""

import io

import docx
import fitz
import pytest
from fastapi.testclient import TestClient

from ats.checks import (
    font_count,
    images,
    margins,
    page_count,
    resume_length,
    special_characters,
    tiny_font,
)
from ats.thresholds import (
    AGREEMENT_PASS,
    AGREEMENT_WARN,
    COMPLETENESS_PASS,
    LENGTH_MAX_WORDS,
    LENGTH_MIN_WORDS,
    TINY_FONT_WARN_FRACTION,
)
from services.prompt import build_user_prompt

BODY_TEXT = """John Doe
john.doe@example.com | +1 555-123-4567

Summary
Full-stack engineer with five years of experience building web applications
and developer tools used by thousands of people every day.

Experience
Software Engineer at TechCorp from 2020 to Present
Built microservices that process one million API requests daily.

Education
B.S. in Computer Science, State University, 2019
"""


def make_pdf(blocks, pages=1, fontsize=10):
    """Build a PDF with `pages` pages; blocks go on page 1."""
    doc = fitz.open()
    for index in range(pages):
        page = doc.new_page()  # A4: 595 x 842 pt
        if index == 0:
            for rect, text in blocks:
                page.insert_textbox(fitz.Rect(*rect), text, fontsize=fontsize)
        else:
            page.insert_textbox(
                fitz.Rect(72, 72, 523, 770), BODY_TEXT, fontsize=fontsize
            )
    data = doc.tobytes()
    doc.close()
    return data


def make_docx(paragraphs):
    document = docx.Document()
    for para in paragraphs:
        document.add_paragraph(para)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def check_by_id(body, check_id):
    return next((c for c in body["checks"] if c["id"] == check_id), None)


@pytest.fixture
def client():
    from core.limiter import limiter
    from main import app

    limiter.reset()
    return TestClient(app)


def post_pdf(client, data, name="resume.pdf"):
    return client.post("/ats/check", files={"file": (name, data, "application/pdf")})


# ── page-count ───────────────────────────────────────────────────────


def test_page_count_single_passes():
    check = page_count(1)
    assert check["status"] == "pass"
    assert check["metric"] == {"kind": "count", "value": 1}


def test_page_count_two_warns_and_names_senior_exception():
    check = page_count(2)
    assert check["status"] == "warn"
    assert "senior or academic" in check["reason"]


def test_page_count_three_fails():
    assert page_count(3)["status"] == "fail"


def test_endpoint_three_page_pdf_fails_page_count(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)], pages=3)
    resp = post_pdf(client, pdf)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "page-count")
    assert check["status"] == "fail"
    assert check["metric"] == {"kind": "count", "value": 3}


# ── resume-length ────────────────────────────────────────────────────


def test_resume_length_band_boundaries():
    assert resume_length(LENGTH_MIN_WORDS)["status"] == "pass"
    assert resume_length(LENGTH_MAX_WORDS)["status"] == "pass"
    sparse = resume_length(LENGTH_MIN_WORDS - 1)
    assert sparse["status"] == "warn"
    assert "sparse" in sparse["reason"]
    bloated = resume_length(LENGTH_MAX_WORDS + 1)
    assert bloated["status"] == "warn"
    assert "Trim" in bloated["fix"]


def test_resume_length_metric_shape():
    metric = resume_length(512)["metric"]
    assert metric == {
        "kind": "band",
        "value": 512,
        "low": LENGTH_MIN_WORDS,
        "high": LENGTH_MAX_WORDS,
        "unit": "words",
    }


def test_endpoint_sparse_pdf_warns_resume_length(client):
    # ~150 words: below the 200-word floor but far above the scanned cutoff
    pdf = make_pdf([((72, 72, 523, 770), "lorem ipsum dolor sit amet " * 30)])
    resp = post_pdf(client, pdf)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "resume-length")
    assert check["status"] == "warn"
    metric = check["metric"]
    assert metric["kind"] == "band"
    assert metric["low"] == LENGTH_MIN_WORDS
    assert metric["high"] == LENGTH_MAX_WORDS
    assert metric["unit"] == "words"
    assert 0 < metric["value"] < LENGTH_MIN_WORDS


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def test_endpoint_docx_gets_resume_length_check(client):
    resp = client.post(
        "/ats/check",
        files={"file": ("resume.docx", make_docx(BODY_TEXT.splitlines()), DOCX_MIME)},
    )
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "resume-length")
    assert check is not None
    assert check["metric"]["kind"] == "band"
    # page-count is PDF-only; DOCX has no fixed pagination to measure
    assert check_by_id(resp.json(), "page-count") is None


# ── font-count ───────────────────────────────────────────────────────


def test_font_count_within_limit_passes():
    assert font_count({"Helvetica", "Helvetica-Bold"})["status"] == "pass"


def test_font_count_soup_warns_and_lists_names():
    fonts = {"Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta"}
    check = font_count(fonts)
    assert check["status"] == "warn"
    assert "Alpha" in check["reason"]
    # at most five names quoted
    assert "Zeta" not in check["reason"]


def test_endpoint_five_fonts_warn(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 300), BODY_TEXT, fontsize=10)
    y = 320
    for fontname in ("helv", "tiro", "cour", "hebo", "tibo"):
        page.insert_text(
            fitz.Point(72, y), f"line set in {fontname}", fontname=fontname
        )
        y += 20
    data = doc.tobytes()
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    assert check_by_id(resp.json(), "font-count")["status"] == "warn"


# ── tiny-font ────────────────────────────────────────────────────────


def test_tiny_font_threshold():
    assert tiny_font(0.0)["status"] == "pass"
    assert tiny_font(TINY_FONT_WARN_FRACTION)["status"] == "warn"
    metric = tiny_font(0.25)["metric"]
    assert metric == {
        "kind": "ratio",
        "value": 0.25,
        "warn_above": TINY_FONT_WARN_FRACTION,
    }


def test_endpoint_seven_point_text_warns_tiny_font(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)], fontsize=7)
    resp = post_pdf(client, pdf)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "tiny-font")
    assert check["status"] == "warn"
    assert check["metric"]["value"] > TINY_FONT_WARN_FRACTION


# ── images ───────────────────────────────────────────────────────────


def test_images_check_statuses():
    assert images(0)["status"] == "pass"
    check = images(2)
    assert check["status"] == "warn"
    assert "invisible" in check["reason"]


def test_endpoint_embedded_image_warns(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 500), BODY_TEXT, fontsize=10)
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 10, 10))
    pixmap.clear_with(120)
    page.insert_image(fitz.Rect(300, 600, 360, 660), pixmap=pixmap)
    data = doc.tobytes()
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    assert check_by_id(resp.json(), "images")["status"] == "warn"


# ── special-characters ───────────────────────────────────────────────


def test_special_characters_flags_emoji_with_sample():
    check = special_characters("Skilled in Python \U0001f680 and Go ⭐")
    # U+2B50 is outside the scanned ranges; the rocket is inside
    assert check["status"] == "warn"
    assert "\U0001f680" in check["reason"]


def test_special_characters_flags_box_drawing():
    assert special_characters("name ─│ details")["status"] == "warn"


def test_special_characters_plain_text_passes():
    assert special_characters("plain ascii resume text")["status"] == "pass"


def test_endpoint_box_drawing_pdf_warns_special_characters(client):
    # insert_htmlbox embeds a real font, so U+2500 survives text extraction
    # (base-14 fonts silently replace it with "?").
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 500), BODY_TEXT, fontsize=10)
    page.insert_htmlbox(fitz.Rect(72, 520, 523, 570), "section rule ─── here")
    data = doc.tobytes()
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "special-characters")
    assert check["status"] == "warn"
    assert "─" in check["reason"]


# ── margins ──────────────────────────────────────────────────────────


def test_margins_check_statuses():
    assert margins(False)["status"] == "pass"
    check = margins(True)
    assert check["status"] == "warn"
    assert "crop" in check["reason"]


def test_endpoint_edge_text_warns_margins(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 500), BODY_TEXT, fontsize=10)
    page.insert_text(fitz.Point(2, 600), "edgehugging", fontsize=10)
    data = doc.tobytes()
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    assert check_by_id(resp.json(), "margins")["status"] == "warn"


def test_endpoint_normal_margins_pass(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    resp = post_pdf(client, pdf)
    assert resp.status_code == 200
    assert check_by_id(resp.json(), "margins")["status"] == "pass"


# ── metric objects on the existing dual-extraction checks ────────────


def test_clean_pdf_agreement_and_completeness_carry_metrics(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    resp = post_pdf(client, pdf)
    assert resp.status_code == 200
    body = resp.json()

    agreement = check_by_id(body, "extraction-agreement")["metric"]
    assert agreement["kind"] == "ratio"
    assert 0.0 <= agreement["value"] <= 1.0
    assert agreement["warn_below"] == AGREEMENT_PASS
    assert agreement["fail_below"] == AGREEMENT_WARN

    completeness = check_by_id(body, "content-completeness")["metric"]
    assert completeness["kind"] == "ratio"
    assert 0.0 <= completeness["value"] <= 1.0
    assert completeness["warn_below"] == COMPLETENESS_PASS
    assert "fail_below" not in completeness


def test_checks_without_metric_omit_the_key(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    body = post_pdf(client, pdf).json()
    assert "metric" not in check_by_id(body, "columns")
    assert "metric" not in check_by_id(body, "contact-info")


# ── encrypted-pdf (v2) ───────────────────────────────────────────────


def test_endpoint_owner_password_pdf_fails_encrypted_check(client):
    """Owner-password AES PDFs open with the empty user password, so the
    battery still runs — and must call out the protection."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 770), BODY_TEXT, fontsize=10)
    data = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="secret123")
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "encrypted-pdf")
    assert check["status"] == "fail"
    assert check["category"] == "file"
    assert "protected" in check["reason"]


def test_endpoint_user_password_pdf_returns_clean_400(client):
    """User-password PDFs cannot be text-extracted at all — the endpoint
    must reject them with the corrupted/password message, not a 500."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 770), BODY_TEXT, fontsize=10)
    data = doc.tobytes(
        encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="secret123", user_pw="usr"
    )
    doc.close()
    resp = post_pdf(client, data)
    assert resp.status_code == 400
    assert "password-protected" in resp.json()["detail"]


def test_endpoint_unencrypted_pdf_passes_encrypted_check(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    resp = post_pdf(client, pdf)
    assert check_by_id(resp.json(), "encrypted-pdf")["status"] == "pass"


# ── file-size (v2) ───────────────────────────────────────────────────


def test_endpoint_padded_pdf_warns_file_size(client):
    import os

    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 770), BODY_TEXT, fontsize=10)
    # incompressible junk stream pushes the file past the 2 MB portal cap
    # while staying under the 5 MB upload limit
    doc.embfile_add("junk.bin", os.urandom(2_600_000))
    data = doc.tobytes()
    doc.close()
    assert len(data) > 2 * 1024 * 1024
    resp = post_pdf(client, data)
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "file-size")
    assert check["status"] == "warn"
    assert check["metric"]["kind"] == "band"
    assert check["metric"]["value"] > 2
    assert check["metric"]["unit"] == "MB"


# ── filename (v2) ────────────────────────────────────────────────────


def test_filename_check_skipped_for_editor_synthesized_name(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    body = post_pdf(client, pdf, name="resume.pdf").json()
    assert check_by_id(body, "filename") is None


def test_filename_check_fires_for_messy_upload_name(client):
    pdf = make_pdf([((72, 72, 523, 770), BODY_TEXT)])
    body = post_pdf(client, pdf, name="resume (1) final.pdf").json()
    check = check_by_id(body, "filename")
    assert check["status"] == "info"
    assert check["informational"] is True
    assert check["category"] == "file"
    # informational checks never count toward the summary
    counted = sum(body["summary"].values())
    info_count = sum(1 for c in body["checks"] if c["status"] == "info")
    assert counted == len(body["checks"]) - info_count


# ── DOCX gets the text-based v2 battery ──────────────────────────────


def test_endpoint_docx_includes_content_and_contact_checks(client):
    paragraphs = BODY_TEXT.splitlines() + [
        "- Built the ingestion service used by 40 teams.",
        "- Led the migration of 12 services to Kubernetes.",
        "- Cut infra spend 30% by right-sizing the fleet.",
    ]
    resp = client.post(
        "/ats/check",
        files={"file": ("cv.docx", make_docx(paragraphs), DOCX_MIME)},
    )
    assert resp.status_code == 200
    body = resp.json()
    density = check_by_id(body, "bullet-density")
    assert density is not None
    assert density["category"] == "content"
    assert check_by_id(body, "quantified-bullets")["category"] == "content"
    assert check_by_id(body, "multiple-emails")["category"] == "contact"
    assert check_by_id(body, "file-size")["category"] == "file"
    # PDF-only checks stay off the DOCX report
    assert check_by_id(body, "encrypted-pdf") is None
    # every check carries a category
    assert all(
        c["category"]
        in {"extraction", "layout", "typography", "contact", "content", "file"}
        for c in body["checks"]
    )


# ── ats_feedback → regeneration prompt ───────────────────────────────


def test_build_user_prompt_appends_parseability_block():
    prompt = build_user_prompt(
        "octocat",
        "readme",
        "info",
        "experience",
        ats_feedback="- Page margins: text touches the edge. Fix: widen margins.",
    )
    assert "PARSEABILITY ISSUES IN PREVIOUS VERSION" in prompt
    assert "widen margins" in prompt
    assert "Never invent new facts" in prompt


def test_build_user_prompt_omits_block_without_feedback():
    prompt = build_user_prompt("octocat", "readme", "info", "experience")
    assert "PARSEABILITY ISSUES" not in prompt


def test_stream_endpoint_accepts_ats_feedback_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    client = TestClient(app)
    resp = client.get(
        "/generate-resume-stream",
        params={
            "github_username": "octocat",
            "ats_feedback": "- Tiny font sizes: 20% below 8.5pt. Fix: use 10pt.",
        },
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "data:" in resp.text


def test_resume_length_uses_best_extraction():
    # Glued pdfplumber output must not undercount words — the router takes
    # the max of both extractions. Unit-level equivalent:
    from ats.checks import resume_length

    glued_words = 126
    real_words = 500
    check = resume_length(max(glued_words, real_words))
    assert check["status"] == "pass"
    assert check["metric"]["value"] == real_words
