"""Tests for ats.extraction — rules-based field extraction (stage 3 part 1).

Pure-string tests for extract_fields_rules plus one endpoint test asserting
the /ats/check response carries the "extracted" block.
"""

import fitz
import pytest
from fastapi.testclient import TestClient

from ats.extraction import extract_fields_rules

RESUME_TEXT = """Jane Doe
jane@x.com | +1 555-123-4567 | linkedin.com/in/janedoe | github.com/janedoe

Summary
Engineer at Acme.

Experience
Software Engineer, Jan 2020 – Present
Data Analyst, 2019–2022
Intern, 05/2016

Education
B.S. Computer Science
"""


def make_pdf(text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 770), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


@pytest.fixture
def client():
    from core.limiter import limiter
    from main import app

    limiter.reset()
    return TestClient(app)


def test_email_found_high():
    result = extract_fields_rules(RESUME_TEXT)["email"]
    assert result.value == "jane@x.com"
    assert result.confidence == "high"
    assert result.method == "regex"
    assert result.failed is False


def test_phone_found():
    result = extract_fields_rules(RESUME_TEXT)["phone"]
    assert result.value == "+1 555-123-4567"
    assert result.failed is False


def test_malformed_phone_fails():
    result = extract_fields_rules("Jane Doe\nphone: 12345\n")["phone"]
    assert result.value is None
    assert result.failed is True


def test_no_phone_is_not_failed():
    result = extract_fields_rules("Jane Doe\njane@x.com\n")["phone"]
    assert result.value is None
    assert result.failed is False


def test_linkedin_and_github_handles():
    fields = extract_fields_rules(RESUME_TEXT)
    assert fields["linkedin"].value == "linkedin.com/in/janedoe"
    assert fields["github"].value == "github.com/janedoe"


def test_name_heuristic_first_line():
    result = extract_fields_rules("Jane Doe\njane@x.com\nExperience\n")["name"]
    assert result.value == "Jane Doe"
    assert result.method == "heuristic"
    assert result.confidence == "high"


def test_name_absent_not_failed():
    text = "EXPERIENCE\nBuilt 3 services in 2021 at Acme Corp\njane@x.com\n"
    result = extract_fields_rules(text)["name"]
    assert result.value is None
    assert result.failed is False
    assert result.confidence == "low"


def test_dates_variants():
    dates = extract_fields_rules(RESUME_TEXT)["dates"].value
    assert "Jan 2020 – Present" in dates
    assert "2019–2022" in dates
    assert "05/2016" in dates


def test_sections_list():
    sections = extract_fields_rules(RESUME_TEXT)["sections"].value
    assert sections == ["education", "experience", "summary"]


def test_endpoint_includes_extracted(client):
    resp = client.post(
        "/ats/check",
        files={"file": ("resume.pdf", make_pdf(RESUME_TEXT), "application/pdf")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "extracted" in body
    email = body["extracted"]["email"]
    assert email["value"] == "jane@x.com"
    assert email["confidence"] == "high"
    # checks/summary shape unchanged
    assert {"passed", "warned", "failed"} <= set(body["summary"])
