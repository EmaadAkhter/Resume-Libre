"""Tests for the composable profile-source rows: the `profiles` request
param, scalar/profiles normalization, and the multi-fetch pipeline loop."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from routers.generation import _normalize_profiles
from schemas.resume import ProfileRef
from services.pipeline import ResumePipeline


@pytest.fixture
def demo_client(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    from core.limiter import limiter
    from main import app

    limiter.reset()
    return TestClient(app)


# ── ProfileRef validation via the endpoints ──────────────────────────


def test_post_rejects_unknown_profile_type(demo_client):
    resp = demo_client.post(
        "/generate-resume",
        json={"profiles": [{"type": "gitlab", "value": "someone"}]},
    )
    assert resp.status_code == 422


def test_post_rejects_more_than_ten_profiles(demo_client):
    profiles = [{"type": "github", "value": f"user{i}"} for i in range(11)]
    resp = demo_client.post("/generate-resume", json={"profiles": profiles})
    assert resp.status_code == 422


def test_post_rejects_blank_profile_value(demo_client):
    resp = demo_client.post(
        "/generate-resume",
        json={"profiles": [{"type": "github", "value": ""}]},
    )
    assert resp.status_code == 422


def test_post_accepts_profiles_only_payload_in_demo_mode(demo_client):
    """A single non-GitHub row is a valid sole source — no scalars needed."""
    resp = demo_client.post(
        "/generate-resume",
        json={"profiles": [{"type": "orcid", "value": "0000-0002-1825-0097"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


# ── stream endpoint `profiles` query param ───────────────────────────


def test_stream_rejects_garbage_json_profiles(demo_client):
    resp = demo_client.get(
        "/generate-resume-stream", params={"profiles": "not-even-json"}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "invalid profiles parameter"


def test_stream_rejects_non_list_profiles_json(demo_client):
    resp = demo_client.get(
        "/generate-resume-stream",
        params={"profiles": json.dumps({"type": "github", "value": "x"})},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "invalid profiles parameter"


def test_stream_rejects_invalid_entry_in_profiles_json(demo_client):
    resp = demo_client.get(
        "/generate-resume-stream",
        params={"profiles": json.dumps([{"type": "gitlab", "value": "x"}])},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "invalid profiles parameter"


def test_stream_rejects_more_than_ten_profiles_entries(demo_client):
    profiles = [{"type": "github", "value": f"user{i}"} for i in range(11)]
    resp = demo_client.get(
        "/generate-resume-stream", params={"profiles": json.dumps(profiles)}
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "invalid profiles parameter"


def test_stream_valid_profiles_json_in_demo_mode(demo_client):
    profiles = [
        {"type": "github", "value": "octocat"},
        {"type": "huggingface", "value": "acme"},
    ]
    resp = demo_client.get(
        "/generate-resume-stream", params={"profiles": json.dumps(profiles)}
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert "data:" in resp.text


# ── scalar/profiles normalization ────────────────────────────────────


def test_normalize_dedupes_scalar_and_profiles_overlap():
    normalized = _normalize_profiles(
        [ProfileRef(type="github", value="octocat")],
        github_username="  octocat  ",
        hf_username="acme",
    )
    assert [(p.type, p.value.strip()) for p in normalized] == [
        ("github", "octocat"),
        ("huggingface", "acme"),
    ]


def test_normalize_appends_scalars_as_rows():
    normalized = _normalize_profiles(
        None,
        github_username="octocat",
        linkedin_url="https://linkedin.com/in/octo",
        hf_username="acme",
        orcid_id="0000-0002-1825-0097",
    )
    assert [(p.type, p.value) for p in normalized] == [
        ("github", "octocat"),
        ("linkedin", "https://linkedin.com/in/octo"),
        ("huggingface", "acme"),
        ("orcid", "0000-0002-1825-0097"),
    ]


def test_normalize_keeps_multiple_rows_of_same_type():
    normalized = _normalize_profiles(
        [
            ProfileRef(type="github", value="work-account"),
            ProfileRef(type="github", value="personal-account"),
        ]
    )
    assert len(normalized) == 2


def test_normalize_caps_at_ten_rows():
    rows = [ProfileRef(type="github", value=f"user{i}") for i in range(9)]
    normalized = _normalize_profiles(
        rows, linkedin_url="https://linkedin.com/in/a", orcid_id="0000-0002-1825-0097"
    )
    assert len(normalized) == 10


# ── pipeline multi-fetch loop ────────────────────────────────────────


def _fetch_patches():
    return (
        patch("services.pipeline.fetch_github_readme", new_callable=AsyncMock),
        patch("services.pipeline.fetch_linkedin_profile", new_callable=AsyncMock),
        patch("services.pipeline.fetch_huggingface_profile", new_callable=AsyncMock),
        patch("services.pipeline.fetch_orcid_profile", new_callable=AsyncMock),
    )


async def test_pipeline_fetches_every_profile_row_and_renders_each():
    pipe = ResumePipeline()
    gh_p, li_p, hf_p, oc_p = _fetch_patches()
    with (
        gh_p as gh,
        li_p as li,
        hf_p as hf,
        oc_p as oc,
        patch(
            "services.pipeline.generate_resume_content", new_callable=AsyncMock
        ) as gen,
    ):
        gh.side_effect = lambda username: f"readme of {username}"
        hf.return_value = {"models": [{"id": "m/x", "downloads": 5, "likes": 1}]}
        gen.return_value = "RESUME"

        result = await pipe.run(
            profiles=[
                {"type": "github", "value": "a"},
                {"type": "github", "value": "b"},
                {"type": "huggingface", "value": "m"},
            ],
            demo=False,
        )

    assert result == "RESUME"
    assert gh.await_count == 2
    gh.assert_any_await("a")
    gh.assert_any_await("b")
    hf.assert_awaited_once_with("m")
    li.assert_not_awaited()
    oc.assert_not_awaited()

    user_prompt = gen.await_args.args[0]
    assert "--- GitHub Profile README: a ---" in user_prompt
    assert "readme of a" in user_prompt
    assert "--- GitHub Profile README: b ---" in user_prompt
    assert "readme of b" in user_prompt
    assert "HuggingFace Profile: m" in user_prompt


async def test_pipeline_converts_legacy_scalars_when_no_profiles_given():
    pipe = ResumePipeline()
    gh_p, li_p, hf_p, oc_p = _fetch_patches()
    with (
        gh_p as gh,
        li_p as li,
        hf_p,
        oc_p,
        patch(
            "services.pipeline.generate_resume_content", new_callable=AsyncMock
        ) as gen,
    ):
        gh.return_value = "legacy readme"
        li.return_value = {"fullname": "Octo Cat"}
        gen.return_value = "RESUME"

        await pipe.run(
            github_username="legacy",
            linkedin_url="https://linkedin.com/in/octo",
            demo=False,
        )

    gh.assert_awaited_once_with("legacy")
    li.assert_awaited_once_with("https://linkedin.com/in/octo")
    user_prompt = gen.await_args.args[0]
    assert "--- GitHub Profile README: legacy ---" in user_prompt
    assert "legacy readme" in user_prompt
    assert "--- LinkedIn Profile ---" in user_prompt
    assert "Name: Octo Cat" in user_prompt


async def test_pipeline_omits_blocks_for_failed_fetches():
    pipe = ResumePipeline()
    gh_p, li_p, hf_p, oc_p = _fetch_patches()
    with (
        gh_p as gh,
        li_p,
        hf_p as hf,
        oc_p,
        patch(
            "services.pipeline.generate_resume_content", new_callable=AsyncMock
        ) as gen,
    ):
        gh.return_value = ""  # fetch failed → no readme
        hf.return_value = {}  # fetch failed → no data
        gen.return_value = "RESUME"

        await pipe.run(
            profiles=[
                {"type": "github", "value": "ghost"},
                {"type": "huggingface", "value": "ghost"},
            ],
            additional_info="hire me",
            demo=False,
        )

    user_prompt = gen.await_args.args[0]
    assert "GitHub Profile README" not in user_prompt
    assert "(No GitHub profile content available)" in user_prompt
    assert "HuggingFace Profile" not in user_prompt
    assert "hire me" in user_prompt


async def test_pipeline_run_stream_accepts_profiles():
    pipe = ResumePipeline()
    captured = {}

    async def fake_stream(prompt, *args, **kwargs):
        captured["prompt"] = prompt
        yield "tok1"
        yield "tok2"

    gh_p, li_p, hf_p, oc_p = _fetch_patches()
    with (
        gh_p as gh,
        li_p,
        hf_p,
        oc_p,
        patch("services.pipeline.generate_resume_stream", fake_stream),
    ):
        gh.return_value = "streamed readme"
        tokens = [
            token
            async for token in pipe.run_stream(
                profiles=[ProfileRef(type="github", value="streamer")],
                demo=False,
            )
        ]

    assert tokens == ["tok1", "tok2"]
    gh.assert_awaited_once_with("streamer")
    assert "--- GitHub Profile README: streamer ---" in captured["prompt"]
