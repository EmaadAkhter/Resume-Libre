"""Tests for the ats-checker v1.1 additions: glued-words diagnosis,
hyperlink-only contact, margin-contact detection, section synonyms,
skills extraction, and informational writing tips."""

import fitz
import pytest
from fastapi.testclient import TestClient

from ats.checks import (
    content_completeness,
    detect_glued,
    extraction_agreement,
    link_only_contact,
    writing_tips,
)
from ats.extraction import extract_fields_rules, find_sections
from ats.skills import ROLE_KEYWORDS, TAXONOMY, extract_skills

# Single-letter words: removing the spaces drops the sequence ratio well
# below the pass threshold, mimicking a kerning-broken extraction.
SPACED_TEXT = "a b c d e f g h i j k l m n o p q r s t"
GLUED_TEXT = SPACED_TEXT.replace(" ", "")

BODY_TEXT = """John Doe
john.doe@example.com | +1 555-123-4567

Summary
Full-stack engineer with five years of experience building web applications
and developer tools used by thousands of people every day.

Experience
Software Engineer at TechCorp from 2020 to Present

Education
B.S. in Computer Science, State University, 2019
"""

NO_CONTACT_BODY = """Summary
Full-stack engineer with five years of experience building web applications
and developer tools used by thousands of people every day.

Experience
Software Engineer at TechCorp from twenty-twenty to Present

Education
B.S. in Computer Science, State University
"""


@pytest.fixture
def client():
    from core.limiter import limiter
    from main import app

    limiter.reset()
    return TestClient(app)


def post_pdf(client, data):
    return client.post(
        "/ats/check", files={"file": ("resume.pdf", data, "application/pdf")}
    )


def check_by_id(body, check_id):
    return next((c for c in body["checks"] if c["id"] == check_id), None)


# ── glued-words diagnosis ────────────────────────────────────────────


def test_detect_glued_true_for_missing_spaces():
    assert detect_glued(SPACED_TEXT, GLUED_TEXT) is True


def test_detect_glued_false_for_similar_texts():
    assert detect_glued(SPACED_TEXT, SPACED_TEXT) is False


def test_detect_glued_empty_texts():
    assert detect_glued("", "") is False


def test_agreement_glued_reason_names_word_counts():
    check = extraction_agreement(SPACED_TEXT, GLUED_TEXT, glued=True)
    assert check["status"] in ("warn", "fail")
    assert "without word spacing" in check["reason"]
    assert "1 words vs 20 words" in check["reason"]
    assert "design-tool" in check["fix"]


def test_agreement_not_glued_keeps_generic_reason():
    check = extraction_agreement(SPACED_TEXT, GLUED_TEXT, glued=False)
    assert "ratio" in check["reason"]


def test_completeness_glued_reason_points_upward():
    check = content_completeness(SPACED_TEXT, GLUED_TEXT, glued=True)
    assert check["status"] == "warn"
    assert "word-spacing issue above" in check["reason"]


# ── hyperlink-only contact ───────────────────────────────────────────


def test_links_fill_missing_contact_fields():
    fields = extract_fields_rules(
        "Jane Doe\nEngineer\n",
        links=["mailto:jane@x.com", "https://github.com/janedoe"],
    )
    assert fields["email"].value == "jane@x.com"
    assert fields["email"].method == "heuristic"
    assert fields["email"].confidence == "low"
    assert fields["github"].value == "https://github.com/janedoe"


def test_links_never_override_visible_text():
    fields = extract_fields_rules(
        "Jane Doe\njane@x.com\n", links=["mailto:other@y.com"]
    )
    assert fields["email"].value == "jane@x.com"
    assert fields["email"].method == "regex"


def test_link_only_contact_check_names_fields():
    fields = extract_fields_rules(
        "Jane Doe\nEngineer\n", links=["https://github.com/janedoe"]
    )
    check = link_only_contact(fields)
    assert check["status"] == "warn"
    assert "github" in check["reason"]
    assert "visible text" in check["fix"]


def test_link_only_contact_passes_without_link_fields():
    fields = extract_fields_rules("Jane Doe\njane@x.com\n")
    assert link_only_contact(fields)["status"] == "pass"


def test_endpoint_link_annotation_pdf(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 100, 523, 700), NO_CONTACT_BODY, fontsize=10)
    page.insert_link(
        {
            "kind": fitz.LINK_URI,
            "from": fitz.Rect(72, 700, 200, 715),
            "uri": "https://github.com/janedoe",
        }
    )
    data = doc.tobytes()
    doc.close()

    resp = post_pdf(client, data)
    assert resp.status_code == 200
    body = resp.json()
    github = body["extracted"]["github"]
    assert github["value"] == "https://github.com/janedoe"
    assert github["confidence"] == "low"
    assert github["method"] == "heuristic"
    check = check_by_id(body, "link-only-contact")
    assert check["status"] == "warn"
    assert "github" in check["reason"]


# ── margin-contact (#25) ─────────────────────────────────────────────


def make_margin_pdf(email_in_margin):
    doc = fitz.open()
    page = doc.new_page()  # A4: 595 x 842 pt; margin band = top/bottom 8%
    if email_in_margin:
        page.insert_text(fitz.Point(72, 30), "john.doe@example.com", fontsize=9)
        body = NO_CONTACT_BODY
    else:
        body = BODY_TEXT
    page.insert_textbox(fitz.Rect(72, 150, 523, 700), body, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


def test_margin_only_email_fails_header_footer_check(client):
    resp = post_pdf(client, make_margin_pdf(email_in_margin=True))
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "header-footer-contact")
    assert check["status"] == "fail"
    assert "header/footer" in check["reason"]


def test_body_contact_passes_header_footer_check(client):
    resp = post_pdf(client, make_margin_pdf(email_in_margin=False))
    assert resp.status_code == 200
    check = check_by_id(resp.json(), "header-footer-contact")
    assert check["status"] == "pass"


# ── section synonyms ─────────────────────────────────────────────────


def test_section_synonyms_map_to_canonical():
    text = "WORK EXPERIENCE\nBuilt things\nACADEMIC QUALIFICATIONS\nB.S.\n"
    assert find_sections(text) == ["education", "experience"]


def test_section_synonyms_dedupe_with_canonical():
    text = "Experience\nstuff\nEmployment\nstuff\nObjective\nstuff\n"
    assert find_sections(text) == ["experience", "summary"]


# ── skills taxonomy ──────────────────────────────────────────────────


def test_extract_skills_basic():
    assert extract_skills("Python and React and Docker") == [
        "Docker",
        "Python",
        "React",
    ]


def test_extract_skills_word_boundaries():
    # "Java" must not match inside "JavaScript".
    assert extract_skills("JavaScript only") == ["JavaScript"]


def test_skills_field_in_extraction():
    result = extract_fields_rules("Skills\nPython, SQL, Docker\n")["skills"]
    assert result.value == ["Docker", "Python", "SQL"]
    assert result.method == "regex"
    assert result.confidence == "high"


def test_skills_field_none_when_empty():
    result = extract_fields_rules("nothing relevant here")["skills"]
    assert result.value is None


def test_role_keywords_shape():
    assert len(ROLE_KEYWORDS) == 10
    assert "General / Fresher" in ROLE_KEYWORDS
    assert TAXONOMY == sorted(TAXONOMY, key=str.lower)
    assert len(TAXONOMY) == len(set(TAXONOMY))


# ── writing tips (informational) ─────────────────────────────────────


def test_writing_tips_matches_weak_phrases():
    check = writing_tips("- worked on backend services\n- Built the API\n")
    assert check["status"] == "info"
    assert check["informational"] is True
    assert "worked on backend services" in check["reason"]
    assert "developed" in check["fix"]


def test_writing_tips_absent_without_weak_phrases():
    assert writing_tips("- Built the API\n- Led the migration\n") is None


def test_endpoint_summary_excludes_info_checks(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(
        fitz.Rect(72, 100, 523, 700),
        BODY_TEXT + "\n- worked on backend services\n",
        fontsize=10,
    )
    data = doc.tobytes()
    doc.close()

    resp = post_pdf(client, data)
    assert resp.status_code == 200
    body = resp.json()
    tips = check_by_id(body, "writing-tips")
    assert tips["status"] == "info"
    assert tips["informational"] is True
    summary = body["summary"]
    counted = summary["passed"] + summary["warned"] + summary["failed"]
    info_count = sum(1 for c in body["checks"] if c["status"] == "info")
    assert info_count == 1
    assert counted == len(body["checks"]) - info_count
    assert "score" not in body
