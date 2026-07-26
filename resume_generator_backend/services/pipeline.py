from collections.abc import Callable
from typing import Any

from core.event_types import Events
from services.events import bus
from services.genrate_resume import generate_resume_content, generate_resume_stream
from services.github import fetch_github_readme
from services.huggingface import fetch_huggingface_profile
from services.linkedin import fetch_linkedin_profile
from services.orcid import fetch_orcid_profile
from services.prompt import build_user_prompt


def _as_profile_tuples(
    profiles: list | None,
    github_username: str = "",
    linkedin_url: str = "",
    hf_username: str = "",
    orcid_id: str = "",
) -> list[tuple[str, str]]:
    """Normalize profile refs (ProfileRef objects or dicts) to (type, value).

    Legacy scalar params are folded in only when no profile rows were given —
    the router already merges scalars into `profiles`; this covers direct
    callers and older tests.
    """
    refs: list[tuple[str, str]] = []
    for ref in profiles or []:
        if isinstance(ref, dict):
            ptype, value = ref.get("type"), ref.get("value")
        else:
            ptype, value = getattr(ref, "type", None), getattr(ref, "value", None)
        ptype = (ptype or "").strip().lower()
        value = (value or "").strip()
        if ptype and value:
            refs.append((ptype, value))

    if not refs:
        for ptype, value in (
            ("github", github_username),
            ("linkedin", linkedin_url),
            ("huggingface", hf_username),
            ("orcid", orcid_id),
        ):
            if value and value.strip():
                refs.append((ptype, value.strip()))
    return refs


class ResumePipeline:
    """Event-driven resume generation pipeline with pluggable middleware.

    Each stage emits events on the EventBus. Middleware functions can be
    registered to intercept/transform data between stages.

    Usage:
        pipeline = ResumePipeline()
        pipeline.on_generation(my_logging_middleware)
        result = await pipeline.run(github_username, additional_info, ...)
    """

    def __init__(self):
        self._middleware: dict[str, list[Callable]] = {
            "readme_fetch": [],
            "prompt_build": [],
            "generation": [],
            "validation": [],
        }

    def on_readme_fetch(self, middleware: Callable) -> None:
        self._middleware["readme_fetch"].append(middleware)

    def on_prompt_build(self, middleware: Callable) -> None:
        self._middleware["prompt_build"].append(middleware)

    def on_generation(self, middleware: Callable) -> None:
        self._middleware["generation"].append(middleware)

    def on_validation(self, middleware: Callable) -> None:
        self._middleware["validation"].append(middleware)

    async def _apply_middleware(self, stage: str, data: Any) -> Any:
        for mw in self._middleware[stage]:
            result = mw(data)
            if result is not None:
                data = result
        return data

    async def _fetch_profiles(
        self, refs: list[tuple[str, str]]
    ) -> tuple[list, list, list, list]:
        """Fetch every profile source row; one bus event per fetch."""
        github_readmes: list[tuple[str, str]] = []
        linkedin_profiles: list[dict] = []
        hf_profiles: list[tuple[str, dict]] = []
        orcid_profiles: list[dict] = []

        for ptype, value in refs:
            if ptype == "github":
                readme = await fetch_github_readme(value)
                readme = await self._apply_middleware("readme_fetch", readme)
                ok = bool(readme)
                if ok:
                    github_readmes.append((value, readme))
            elif ptype == "linkedin":
                data = await fetch_linkedin_profile(value)
                ok = bool(data)
                if ok:
                    linkedin_profiles.append(data)
            elif ptype == "huggingface":
                data = await fetch_huggingface_profile(value)
                ok = bool(data)
                if ok:
                    hf_profiles.append((value, data))
            elif ptype == "orcid":
                data = await fetch_orcid_profile(value)
                ok = bool(data)
                if ok:
                    orcid_profiles.append(data)
            else:
                continue
            await bus.publish(
                Events.README_FETCHED, {"source": ptype, "id": value, "ok": ok}
            )

        return github_readmes, linkedin_profiles, hf_profiles, orcid_profiles

    def _build_prompt_from_profiles(
        self,
        refs: list[tuple[str, str]],
        fetched: tuple[list, list, list, list],
        github_username: str,
        additional_info: str,
        job_description: str,
        priority: str,
        resume_template: str | None,
        ats_feedback: str | None,
    ) -> str:
        github_readmes, linkedin_profiles, hf_profiles, orcid_profiles = fetched
        first_github = (
            next((v for t, v in refs if t == "github"), "")
            or (github_username or "").strip()
        )
        return build_user_prompt(
            first_github,
            "",
            additional_info,
            priority,
            resume_template,
            job_description=job_description,
            ats_feedback=ats_feedback,
            github_readmes=github_readmes,
            linkedin_profiles=linkedin_profiles,
            hf_profiles=hf_profiles,
            orcid_profiles=orcid_profiles,
        )

    async def run(
        self,
        github_username: str = "",
        linkedin_url: str = "",
        hf_username: str = "",
        orcid_id: str = "",
        additional_info: str = "",
        job_description: str = "",
        priority: str = "experience",
        custom_system_prompt: str | None = None,
        resume_template: str | None = None,
        template_format: str = "md",
        ats_feedback: str | None = None,
        demo: bool = False,
        profiles: list | None = None,
    ) -> str:
        """Execute the full pipeline. Returns the generated resume content."""

        if demo:
            return await generate_resume_content("", demo=True)

        refs = _as_profile_tuples(
            profiles, github_username, linkedin_url, hf_username, orcid_id
        )

        # Stage 1: Fetch every profile source
        fetched = await self._fetch_profiles(refs)

        # Stage 2: Build the prompt
        user_prompt = self._build_prompt_from_profiles(
            refs,
            fetched,
            github_username,
            additional_info,
            job_description,
            priority,
            resume_template,
            ats_feedback,
        )
        user_prompt = await self._apply_middleware("prompt_build", user_prompt)
        await bus.publish(Events.PROMPT_BUILT, {"length": len(user_prompt)})

        # Stage 3: Generate resume
        await bus.publish(Events.LLM_GENERATING, {"model": True})
        resume = await generate_resume_content(
            user_prompt, custom_system_prompt, template_format
        )
        resume = await self._apply_middleware("generation", resume)
        await bus.publish(Events.VALIDATION_PASSED, {"length": len(resume)})

        return resume

    async def run_stream(
        self,
        github_username: str = "",
        linkedin_url: str = "",
        hf_username: str = "",
        orcid_id: str = "",
        additional_info: str = "",
        job_description: str = "",
        priority: str = "experience",
        custom_system_prompt: str | None = None,
        resume_template: str | None = None,
        template_format: str = "md",
        ats_feedback: str | None = None,
        demo: bool = False,
        profiles: list | None = None,
    ):
        """Execute the pipeline with streaming generation. Yields tokens."""

        if demo:
            async for token in generate_resume_stream("", demo=True):
                yield token
            return

        refs = _as_profile_tuples(
            profiles, github_username, linkedin_url, hf_username, orcid_id
        )

        # Stage 1: Fetch every profile source
        fetched = await self._fetch_profiles(refs)

        # Stage 2: Build the prompt
        user_prompt = self._build_prompt_from_profiles(
            refs,
            fetched,
            github_username,
            additional_info,
            job_description,
            priority,
            resume_template,
            ats_feedback,
        )
        user_prompt = await self._apply_middleware("prompt_build", user_prompt)
        await bus.publish(Events.PROMPT_BUILT, {"length": len(user_prompt)})

        # Stage 3: Stream generation
        await bus.publish(Events.LLM_GENERATING, {"streaming": True})

        async for token in generate_resume_stream(
            user_prompt, custom_system_prompt, template_format
        ):
            await bus.publish(Events.LLM_TOKEN, token)
            yield token

        await bus.publish(Events.VALIDATION_PASSED, {"streaming": True})


# Module-level singleton — import this, not the class
pipeline = ResumePipeline()
