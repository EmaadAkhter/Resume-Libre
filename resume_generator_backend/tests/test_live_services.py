"""Tests for the code paths that actually run in production:
GitHub fetch, OpenRouter call error handling, sidecar-down behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException


def _async_client_returning(response=None, error=None):
    """Mock httpx.AsyncClient context manager."""
    client = MagicMock()
    if error:
        client.get = AsyncMock(side_effect=error)
        client.post = AsyncMock(side_effect=error)
    else:
        client.get = AsyncMock(return_value=response)
        client.post = AsyncMock(return_value=response)
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


@pytest.fixture(autouse=True)
def no_redis():
    """Redis unreachable — exercises the cache-miss fallback path."""
    with patch("services.cache.get_redis", side_effect=Exception("no redis")):
        yield


async def test_github_readme_fetch_ok():
    from services.github import fetch_github_readme

    resp = MagicMock(status_code=200, text="# My README")
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        assert await fetch_github_readme("octocat") == "# My README"


async def test_github_readme_fetch_404_returns_empty():
    from services.github import fetch_github_readme

    resp = MagicMock(status_code=404, text="nope")
    with patch("httpx.AsyncClient", return_value=_async_client_returning(resp)):
        assert await fetch_github_readme("ghost") == ""


async def test_github_readme_network_error_returns_empty():
    from services.github import fetch_github_readme

    with patch(
        "httpx.AsyncClient",
        return_value=_async_client_returning(error=httpx.ConnectError("down")),
    ):
        assert await fetch_github_readme("octocat") == ""


async def test_generation_api_error_becomes_500():
    from services.genrate_resume import generate_resume_content

    with patch("services.genrate_resume._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = Exception(
            "quota exceeded"
        )
        with pytest.raises(HTTPException) as exc:
            await generate_resume_content("prompt")
    assert exc.value.status_code == 500


async def test_generation_short_output_rejected():
    from services.genrate_resume import generate_resume_content

    completion = MagicMock()
    completion.choices = [MagicMock(message=MagicMock(content="too short"))]
    with patch("services.genrate_resume._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = completion
        with pytest.raises(HTTPException) as exc:
            await generate_resume_content("prompt")
    assert exc.value.status_code == 500


async def test_sidecar_down_returns_503():
    from services.latex_compiler import compile_latex_pdf

    with patch(
        "httpx.AsyncClient",
        return_value=_async_client_returning(error=httpx.ConnectError("refused")),
    ):
        with pytest.raises(HTTPException) as exc:
            await compile_latex_pdf("\\documentclass{article}\\begin{document}x\\end{document}")
    assert exc.value.status_code == 503


async def test_linkedin_no_token_returns_empty(monkeypatch):
    from services.linkedin import fetch_linkedin_profile

    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    assert await fetch_linkedin_profile("https://linkedin.com/in/x") == {}
