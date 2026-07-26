"""Tests for ats.llm_fallback — LLM fallback field resolution (stage 3 part 2).

Unit tests exercise the double-sampling merge rules with a mocked client;
endpoint tests cover auth, demo mode, and the no-LLM-needed happy path.
"""

import json
from unittest.mock import MagicMock, patch

import fitz
import pytest
from fastapi.testclient import TestClient

from ats.extraction import FieldResult
from ats.llm_fallback import resolve_low_confidence

RESUME_TEXT = """jane doe
somewhere in the city

Experience
worked at a company for a while
"""


def _completion(content: str) -> MagicMock:
    completion = MagicMock()
    completion.choices = [MagicMock()]
    completion.choices[0].message.content = content
    return completion


def _mock_llm(*replies) -> MagicMock:
    """Client whose successive create() calls return the given payloads.
    A dict is JSON-encoded; an Exception instance/class is raised."""
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        r if isinstance(r, Exception) else _completion(json.dumps(r)) for r in replies
    ]
    return client


def all_high_rules():
    return {
        "email": FieldResult(value="jane@x.com"),
        "phone": FieldResult(value="+1 555-123-4567"),
        "name": FieldResult(value="Jane Doe", method="heuristic"),
    }


# ---------------------------------------------------------------- unit tests


async def test_no_low_confidence_fields_makes_no_llm_call():
    rules = all_high_rules()
    with patch("ats.llm_fallback._get_client") as mock_get_client:
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result == rules
    mock_get_client.assert_not_called()


async def test_agreeing_samples_resolve_to_medium_llm():
    rules = {
        "email": FieldResult(value="jane@x.com"),
        "name": FieldResult(value=None, method="heuristic", confidence="low"),
    }
    llm = _mock_llm({"name": "Jane Doe"}, {"name": "  JANE DOE "})
    with patch("ats.llm_fallback._get_client", return_value=llm):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result["name"].value == "Jane Doe"
    assert result["name"].confidence == "medium"
    assert result["name"].method == "llm"
    assert result["name"].failed is False
    assert result["name"].llm_disagreement is False
    # high-confidence rules result untouched
    assert result["email"] == rules["email"]
    assert llm.chat.completions.create.call_count == 2


async def test_disagreeing_samples_resolve_to_low_with_flag():
    rules = {"name": FieldResult(value=None, method="heuristic", confidence="low")}
    llm = _mock_llm({"name": "Jane Doe"}, {"name": "Janet Doerr"})
    with patch("ats.llm_fallback._get_client", return_value=llm):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result["name"].value == "Jane Doe"  # run1 wins
    assert result["name"].confidence == "low"
    assert result["name"].method == "llm"
    assert result["name"].llm_disagreement is True


async def test_run1_invalid_email_marks_field_failed():
    rules = {"email": FieldResult(value=None, confidence="low")}
    llm = _mock_llm({"email": "not-an-email"}, {"email": "jane@x.com"})
    with patch("ats.llm_fallback._get_client", return_value=llm):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result["email"].value is None
    assert result["email"].failed is True
    assert result["email"].method == "llm"


async def test_one_bad_field_does_not_discard_others():
    rules = {
        "email": FieldResult(value=None, confidence="low"),
        "name": FieldResult(value=None, method="heuristic", confidence="low"),
    }
    llm = _mock_llm(
        {"email": "not-an-email", "name": "Jane Doe"},
        {"email": "also-bad", "name": "Jane Doe"},
    )
    with patch("ats.llm_fallback._get_client", return_value=llm):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result["email"].failed is True
    assert result["name"].value == "Jane Doe"
    assert result["name"].confidence == "medium"


async def test_llm_disagreeing_with_rules_candidate_keeps_rules_value():
    rules = {
        "name": FieldResult(value="Jane Doe", method="heuristic", confidence="low")
    }
    llm = _mock_llm({"name": "Janet Doerr"}, {"name": "Janet Doerr"})
    with patch("ats.llm_fallback._get_client", return_value=llm):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result["name"].value == "Jane Doe"
    assert result["name"].confidence == "low"
    assert result["name"].method == "heuristic"
    assert result["name"].llm_disagreement is True


async def test_both_calls_raising_returns_rules_unchanged():
    rules = {"name": FieldResult(value=None, method="heuristic", confidence="low")}
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("provider down")
    with patch("ats.llm_fallback._get_client", return_value=client):
        result = await resolve_low_confidence(RESUME_TEXT, rules)

    assert result == rules


async def test_demo_merges_canned_resolution_without_client():
    rules = {
        "email": FieldResult(value="jane@x.com"),
        "name": FieldResult(value=None, method="heuristic", confidence="low"),
    }
    with patch("ats.llm_fallback._get_client") as mock_get_client:
        result = await resolve_low_confidence(RESUME_TEXT, rules, demo=True)

    assert result["name"].value == "Jane Doe"
    assert result["name"].confidence == "medium"
    assert result["name"].method == "llm"
    assert result["email"] == rules["email"]
    mock_get_client.assert_not_called()


# ------------------------------------------------------------ endpoint tests


def make_pdf(text):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_textbox(fitz.Rect(72, 72, 523, 770), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


CLEAN_RESUME_TEXT = """Jane Doe
jane@x.com | +1 555-123-4567

Experience
Software Engineer, Jan 2020 – Present

Education
B.S. Computer Science
"""


@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    monkeypatch.delenv("ALLOW_DEMO_REQUESTS", raising=False)
    from core.limiter import limiter
    from main import app

    limiter.reset()
    return TestClient(app)


def post_file(client, data, headers=None):
    return client.post(
        "/ats/extract",
        files={"file": ("resume.pdf", data, "application/pdf")},
        headers=headers or {},
    )


def test_extract_requires_auth(client):
    resp = post_file(client, make_pdf(CLEAN_RESUME_TEXT))
    assert resp.status_code == 401


def test_extract_demo_mode_returns_extracted(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    demo_client = TestClient(app)
    # lowercase first line → the name heuristic stays low-confidence,
    # so the demo canned resolution fills the slot.
    pdf = make_pdf(
        "jane doe\n"
        "jane@x.com | +1 555-123-4567\n\n"
        "Experience\n"
        "worked on backend services and internal tooling for several years,\n"
        "shipping features across the stack with a small product team.\n"
    )
    with patch("ats.llm_fallback._get_client") as mock_get_client:
        resp = post_file(demo_client, pdf)

    assert resp.status_code == 200
    body = resp.json()
    assert body["filename"] == "resume.pdf"
    assert body["extracted"]["name"]["value"] == "Jane Doe"
    assert body["extracted"]["name"]["method"] == "llm"
    assert body["extracted"]["email"]["value"] == "jane@x.com"
    mock_get_client.assert_not_called()


def test_extract_clean_pdf_needs_no_llm(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    demo_client = TestClient(app)
    with patch("ats.llm_fallback._get_client") as mock_get_client:
        resp = post_file(demo_client, make_pdf(CLEAN_RESUME_TEXT))

    assert resp.status_code == 200
    extracted = resp.json()["extracted"]
    # All resolvable fields came out high-confidence from the rules alone.
    assert extracted["name"]["confidence"] == "high"
    assert extracted["email"]["confidence"] == "high"
    assert extracted["phone"]["confidence"] == "high"
    assert all(f["method"] != "llm" for f in extracted.values())
    mock_get_client.assert_not_called()


def test_extract_scanned_pdf_rejected_422(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    demo_client = TestClient(app)
    doc = fitz.open()
    doc.new_page()
    pdf = doc.tobytes()
    doc.close()
    resp = post_file(demo_client, pdf)

    assert resp.status_code == 422
    assert "no extractable text" in resp.json()["detail"]
