"""Tests for POST /ats/check. Fixture PDFs/DOCX are generated in memory
with PyMuPDF / python-docx so no binary fixtures live in the repo."""

import io
import os

import docx
import fitz
import pytest
from fastapi.testclient import TestClient

CLEAN_RESUME_TEXT = """John Doe
john.doe@example.com | +1 555-123-4567 | San Francisco, CA

Summary
Full-stack engineer with five years of experience building web applications
and developer tools used by thousands of people every day.

Experience
Software Engineer at TechCorp from 2020 to Present
Built microservices that process one million API requests daily.
Led the migration from a monolith to microservices architecture.

Education
B.S. in Computer Science, State University, 2019

Skills
Python, JavaScript, Go, PostgreSQL, Docker, Kubernetes
"""

LEFT_COLUMN_TEXT = """Skills
Python JavaScript Go
Docker Kubernetes AWS
PostgreSQL Redis Kafka
Terraform Ansible Git
Linux Nginx GraphQL
"""

RIGHT_COLUMN_TEXT = """Experience
Software Engineer at TechCorp since 2020
Built microservices processing many requests daily
Led migration from monolith to services
Improved deployment speed by a large margin
Mentored junior engineers on the team
"""


def make_pdf(blocks):
    """Build a PDF from (rect, text) blocks and return its bytes."""
    doc = fitz.open()
    page = doc.new_page()  # A4: 595 x 842 pt
    for rect, text in blocks:
        page.insert_textbox(fitz.Rect(*rect), text, fontsize=10)
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
    return next(c for c in body["checks"] if c["id"] == check_id)


@pytest.fixture
def client():
    # mock_env_vars (conftest, autouse) has already set RATE_LIMIT_STORAGE
    # to memory:// before the app is imported here.
    from main import app
    from core.limiter import limiter

    limiter.reset()  # 5/hour would trip across the test session otherwise
    return TestClient(app)


def post_file(client, filename, data, content_type="application/pdf"):
    return client.post(
        "/ats/check", files={"file": (filename, data, content_type)}
    )


def test_clean_single_column_pdf_passes_all_checks(client):
    pdf = make_pdf([((72, 72, 523, 770), CLEAN_RESUME_TEXT)])
    resp = post_file(client, "resume.pdf", pdf)
    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "resume.pdf"
    assert body["summary"] == {"passed": 7, "warned": 0, "failed": 0}
    assert all(c["status"] == "pass" for c in body["checks"])
    assert "score" not in body  # checklist only, no blended score


def test_two_column_pdf_warns_on_columns(client):
    pdf = make_pdf(
        [
            # start below the header band (top 15% of the page) that the
            # column detector deliberately ignores
            ((36, 160, 260, 770), LEFT_COLUMN_TEXT),
            ((330, 160, 559, 770), RIGHT_COLUMN_TEXT),
        ]
    )
    resp = post_file(client, "two-col.pdf", pdf)
    assert resp.status_code == 200
    columns = check_by_id(resp.json(), "columns")
    assert columns["status"] == "warn"
    assert "columns" in columns["reason"]


def test_jpeg_renamed_to_pdf_rejected(client):
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 512
    resp = post_file(client, "photo.pdf", jpeg)
    assert resp.status_code == 400
    assert "not a valid PDF" in resp.json()["detail"]


def test_empty_pdf_reports_scanned_fail(client):
    doc = fitz.open()
    doc.new_page()
    pdf = doc.tobytes()
    doc.close()
    resp = post_file(client, "scan.pdf", pdf)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["checks"]) == 1
    assert body["checks"][0]["id"] == "scanned-pdf"
    assert body["checks"][0]["status"] == "fail"
    assert body["summary"]["failed"] == 1


def test_txt_upload_rejected(client):
    resp = post_file(client, "resume.txt", b"plain text resume", "text/plain")
    assert resp.status_code == 400


def test_docx_agreement_auto_passes(client):
    data = make_docx(CLEAN_RESUME_TEXT.splitlines())
    resp = post_file(
        client,
        "resume.docx",
        data,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert resp.status_code == 200
    body = resp.json()
    assert check_by_id(body, "extraction-agreement")["status"] == "pass"
    assert check_by_id(body, "contact-info")["status"] == "pass"


def test_oversize_upload_rejected(client):
    blob = b"%PDF-" + os.urandom(5 * 1024 * 1024)
    resp = post_file(client, "big.pdf", blob)
    assert resp.status_code == 413
