"""Tests for the HuggingFace and ORCID profile sources (issue #9):
fetchers, prompt blocks, and the generation-endpoint plumbing."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from services.prompt import build_user_prompt


def _async_client_returning(response=None, error=None, responses=None):
    """Mock httpx.AsyncClient context manager.

    `responses` is a list consumed one per GET — for fetchers that hit
    several endpoints on one client.
    """
    client = MagicMock()
    if error:
        client.get = AsyncMock(side_effect=error)
        client.post = AsyncMock(side_effect=error)
    elif responses is not None:
        client.get = AsyncMock(side_effect=responses)
    else:
        client.get = AsyncMock(return_value=response)
        client.post = AsyncMock(return_value=response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _json_response(payload, status_code=200):
    resp = MagicMock(status_code=status_code)
    resp.json.return_value = payload
    return resp


@pytest.fixture(autouse=True)
def no_redis():
    """Redis unreachable — exercises the cache-miss fallback path.

    Patch the names imported into each service module, not services.cache —
    `from services.cache import get_redis` binds a local reference.
    """
    with (
        patch("services.huggingface.get_redis", side_effect=Exception("no redis")),
        patch("services.orcid.get_redis", side_effect=Exception("no redis")),
    ):
        yield


# ── HuggingFace fetcher ──────────────────────────────────────────────


async def test_hf_happy_path_shapes_items_and_omits_empty_sections():
    from services.huggingface import fetch_huggingface_profile

    models = [
        {"id": "acme/big-model", "downloads": 1200, "likes": 30, "private": False},
        {"id": "acme/small-model", "downloads": 7, "likes": 0},
    ]
    datasets = [{"id": "acme/corpus", "downloads": 55, "likes": 2}]
    spaces = []  # spaces endpoint returns an empty list → key omitted

    cm = _async_client_returning(
        responses=[
            _json_response(models),
            _json_response(datasets),
            _json_response(spaces),
        ]
    )
    with patch("httpx.AsyncClient", return_value=cm):
        data = await fetch_huggingface_profile("acme")

    assert data == {
        "models": [
            {"id": "acme/big-model", "downloads": 1200, "likes": 30},
            {"id": "acme/small-model", "downloads": 7, "likes": 0},
        ],
        "datasets": [{"id": "acme/corpus", "downloads": 55, "likes": 2}],
    }
    assert "spaces" not in data


async def test_hf_spaces_have_no_downloads_field():
    from services.huggingface import fetch_huggingface_profile

    spaces = [{"id": "acme/demo-space", "likes": 9}]
    cm = _async_client_returning(
        responses=[_json_response([]), _json_response([]), _json_response(spaces)]
    )
    with patch("httpx.AsyncClient", return_value=cm):
        data = await fetch_huggingface_profile("acme")

    assert data == {"spaces": [{"id": "acme/demo-space", "downloads": 0, "likes": 9}]}


async def test_hf_all_empty_returns_empty_dict():
    # A nonexistent user returns empty lists (not 404) on every endpoint
    from services.huggingface import fetch_huggingface_profile

    cm = _async_client_returning(
        responses=[_json_response([]), _json_response([]), _json_response([])]
    )
    with patch("httpx.AsyncClient", return_value=cm):
        assert await fetch_huggingface_profile("ghost") == {}


async def test_hf_network_error_returns_empty_dict():
    from services.huggingface import fetch_huggingface_profile

    with patch(
        "httpx.AsyncClient",
        return_value=_async_client_returning(error=httpx.ConnectError("down")),
    ):
        assert await fetch_huggingface_profile("acme") == {}


async def test_hf_blank_username_skips_http_entirely():
    from services.huggingface import fetch_huggingface_profile

    with patch("httpx.AsyncClient") as client_cls:
        assert await fetch_huggingface_profile("") == {}
        assert await fetch_huggingface_profile("   ") == {}
    client_cls.assert_not_called()


async def test_hf_pasted_profile_url_is_stripped_to_username():
    from services.huggingface import fetch_huggingface_profile

    cm = _async_client_returning(
        responses=[
            _json_response([{"id": "acme/m", "downloads": 1, "likes": 0}]),
            _json_response([]),
            _json_response([]),
        ]
    )
    with patch("httpx.AsyncClient", return_value=cm):
        data = await fetch_huggingface_profile("https://huggingface.co/acme/")

    called_urls = [
        call.args[0] for call in cm.__aenter__.return_value.get.call_args_list
    ]
    assert all("author=acme" in url for url in called_urls)
    assert data["models"][0]["id"] == "acme/m"


# ── ORCID fetcher ────────────────────────────────────────────────────


def _orcid_record(works_groups=None, employment_groups=None):
    return {
        "orcid-identifier": {"path": "0000-0002-1825-0097"},
        "person": {
            "name": {
                "given-names": {"value": "Josiah"},
                "family-name": {"value": "Carberry"},
                "credit-name": None,
            }
        },
        "activities-summary": {
            "employments": {
                "affiliation-group": employment_groups
                if employment_groups is not None
                else [
                    {
                        "summaries": [
                            {
                                "employment-summary": {
                                    "role-title": "Professor of Psychoceramics",
                                    "organization": {"name": "Brown University"},
                                    "start-date": {"year": {"value": "2008"}},
                                    "end-date": None,
                                }
                            }
                        ]
                    },
                    {
                        "summaries": [
                            {
                                "employment-summary": {
                                    "role-title": "Visiting Scholar",
                                    "organization": {"name": "Wesleyan University"},
                                    "start-date": {"year": {"value": "2001"}},
                                    "end-date": {"year": {"value": "2007"}},
                                }
                            }
                        ]
                    },
                ]
            },
            "educations": {
                "affiliation-group": [
                    {
                        "summaries": [
                            {
                                "education-summary": {
                                    "role-title": "Ph.D. Psychoceramics",
                                    "organization": {"name": "Brown University"},
                                    "start-date": None,
                                    "end-date": {"year": {"value": "1966"}},
                                }
                            }
                        ]
                    }
                ]
            },
            "works": {
                "group": works_groups
                if works_groups is not None
                else [
                    {
                        "work-summary": [
                            {
                                "title": {
                                    "title": {
                                        "value": "Toward a Unified Theory of High-Energy Metaphysics"
                                    }
                                },
                                "publication-date": {"year": {"value": "2008"}},
                            }
                        ]
                    },
                    {
                        # same title from another source — must be deduped
                        "work-summary": [
                            {
                                "title": {
                                    "title": {
                                        "value": "Toward a Unified Theory of High-Energy Metaphysics"
                                    }
                                },
                                "publication-date": None,
                            }
                        ]
                    },
                    {
                        "work-summary": [
                            {
                                "title": {
                                    "title": {
                                        "value": "Bulk and Surface Plasmons in Artificially Structured Materials"
                                    }
                                },
                                "publication-date": {"year": {"value": "1982"}},
                            }
                        ]
                    },
                ]
            },
        },
    }


async def test_orcid_happy_path_extracts_name_works_employments():
    from services.orcid import fetch_orcid_profile

    resp = _json_response(_orcid_record())
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        data = await fetch_orcid_profile("0000-0002-1825-0097")

    assert data["name"] == "Josiah Carberry"
    assert data["employments"] == [
        {
            "org": "Brown University",
            "role": "Professor of Psychoceramics",
            "start": "2008",
            "end": "Present",
        },
        {
            "org": "Wesleyan University",
            "role": "Visiting Scholar",
            "start": "2001",
            "end": "2007",
        },
    ]
    assert data["educations"] == [
        {"org": "Brown University", "degree": "Ph.D. Psychoceramics", "year": "1966"}
    ]
    # duplicate title collapsed: 3 groups → 2 works
    assert [w["title"] for w in data["works"]] == [
        "Toward a Unified Theory of High-Energy Metaphysics",
        "Bulk and Surface Plasmons in Artificially Structured Materials",
    ]
    assert data["works"][0]["year"] == "2008"


async def test_orcid_works_capped_at_15_and_employments_at_5():
    from services.orcid import fetch_orcid_profile

    works = [
        {
            "work-summary": [
                {
                    "title": {"title": {"value": f"Paper {i}"}},
                    "publication-date": {"year": {"value": str(2000 + i)}},
                }
            ]
        }
        for i in range(20)
    ]
    employments = [
        {
            "summaries": [
                {
                    "employment-summary": {
                        "role-title": f"Role {i}",
                        "organization": {"name": f"Org {i}"},
                        "start-date": None,
                        "end-date": None,
                    }
                }
            ]
        }
        for i in range(7)
    ]
    resp = _json_response(
        _orcid_record(works_groups=works, employment_groups=employments)
    )
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        data = await fetch_orcid_profile("0000-0002-1825-0097")

    assert len(data["works"]) == 15
    assert len(data["employments"]) == 5
    assert data["employments"][0]["end"] == "Present"


async def test_orcid_invalid_id_skips_http_entirely():
    from services.orcid import fetch_orcid_profile

    with patch("httpx.AsyncClient") as client_cls:
        assert await fetch_orcid_profile("not-an-orcid") == {}
        assert await fetch_orcid_profile("") == {}
    client_cls.assert_not_called()


async def test_orcid_url_form_and_lowercase_x_normalized():
    from services.orcid import fetch_orcid_profile

    resp = _json_response(_orcid_record())
    cm = _async_client_returning(resp)
    with patch("httpx.AsyncClient", return_value=cm):
        data = await fetch_orcid_profile("https://orcid.org/0000-0002-1825-009x")

    called_url = cm.__aenter__.return_value.get.call_args.args[0]
    assert called_url == "https://pub.orcid.org/v3.0/0000-0002-1825-009X/record"
    assert data["name"] == "Josiah Carberry"


async def test_orcid_404_returns_empty_dict():
    from services.orcid import fetch_orcid_profile

    resp = MagicMock(status_code=404)
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        assert await fetch_orcid_profile("0000-0002-1825-0097") == {}


async def test_orcid_record_without_name_works_or_employments_is_empty():
    from services.orcid import fetch_orcid_profile

    bare = {
        "person": {"name": None},
        "activities-summary": {
            "employments": {"affiliation-group": []},
            "educations": {
                "affiliation-group": [
                    {
                        "summaries": [
                            {
                                "education-summary": {
                                    "role-title": "B.S.",
                                    "organization": {"name": "Somewhere"},
                                    "end-date": {"year": {"value": "1999"}},
                                }
                            }
                        ]
                    }
                ]
            },
            "works": {"group": []},
        },
    }
    resp = _json_response(bare)
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        assert await fetch_orcid_profile("0000-0002-1825-0097") == {}


# ── prompt blocks ────────────────────────────────────────────────────

HF_DATA = {
    "models": [{"id": "acme/big-model", "downloads": 1200, "likes": 30}],
    "spaces": [{"id": "acme/demo-space", "downloads": 0, "likes": 7}],
}

ORCID_DATA = {
    "name": "Josiah Carberry",
    "employments": [
        {
            "org": "Brown University",
            "role": "Professor of Psychoceramics",
            "start": "2008",
            "end": "Present",
        }
    ],
    "educations": [
        {"org": "Brown University", "degree": "Ph.D. Psychoceramics", "year": "1966"}
    ],
    "works": [
        {"title": "Toward a Unified Theory of High-Energy Metaphysics", "year": "2008"},
        {"title": "Undated Manuscript", "year": ""},
    ],
}


def test_build_user_prompt_includes_hf_and_orcid_blocks():
    prompt = build_user_prompt(
        "octocat",
        "readme",
        "info",
        "experience",
        hf_data=HF_DATA,
        orcid_data=ORCID_DATA,
    )
    assert "--- HuggingFace Profile ---" in prompt
    assert "Model: acme/big-model — 1200 downloads, 30 likes" in prompt
    assert "Space: acme/demo-space — 7 likes" in prompt
    assert "Dataset:" not in prompt  # absent sub-section omitted

    assert "--- ORCID Research Profile ---" in prompt
    assert "Name: Josiah Carberry" in prompt
    assert "Affiliations:" in prompt
    assert "- Professor of Psychoceramics, Brown University (2008–Present)" in prompt
    assert "Education:" in prompt
    assert "- Ph.D. Psychoceramics, Brown University (1966)" in prompt
    assert "Publications:" in prompt
    assert "- Toward a Unified Theory of High-Energy Metaphysics (2008)" in prompt
    # a work with no year gets no empty parens
    assert "- Undated Manuscript\n" in prompt


def test_build_user_prompt_omits_blocks_without_data():
    prompt = build_user_prompt("octocat", "readme", "info", "experience")
    assert "HuggingFace Profile" not in prompt
    assert "ORCID Research Profile" not in prompt

    prompt = build_user_prompt(
        "octocat", "readme", "info", "experience", hf_data={}, orcid_data={}
    )
    assert "HuggingFace Profile" not in prompt
    assert "ORCID Research Profile" not in prompt


def test_orcid_block_omits_absent_subsections():
    prompt = build_user_prompt(
        "octocat",
        "readme",
        "info",
        "experience",
        orcid_data={"name": "Josiah Carberry"},
    )
    assert "Name: Josiah Carberry" in prompt
    assert "Affiliations:" not in prompt
    assert "Education:" not in prompt
    assert "Publications:" not in prompt


# ── endpoint plumbing ────────────────────────────────────────────────


def test_generate_endpoint_accepts_profile_sources_in_demo_mode(monkeypatch):
    """Demo mode early-returns before any fetching — the new fields must be
    accepted by the schema and never trigger network calls."""
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    client = TestClient(app)
    with (
        patch(
            "services.pipeline.fetch_huggingface_profile", new_callable=AsyncMock
        ) as hf_mock,
        patch(
            "services.pipeline.fetch_orcid_profile", new_callable=AsyncMock
        ) as orcid_mock,
    ):
        resp = client.post(
            "/generate-resume",
            json={
                "github_username": "octocat",
                "hf_username": "acme",
                "orcid_id": "0000-0002-1825-0097",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"
    hf_mock.assert_not_called()
    orcid_mock.assert_not_called()


def test_stream_endpoint_accepts_profile_sources_in_demo_mode(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    client = TestClient(app)
    resp = client.get(
        "/generate-resume-stream",
        params={
            "github_username": "octocat",
            "hf_username": "acme",
            "orcid_id": "0000-0002-1825-0097",
        },
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "data:" in resp.text
