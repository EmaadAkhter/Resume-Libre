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
    ) -> str:
        """Execute the full pipeline. Returns the generated resume content."""

        if demo:
            return await generate_resume_content("", demo=True)

        # Stage 1: Fetch GitHub README
        readme_content = ""
        if github_username:
            readme_content = await fetch_github_readme(github_username)
            readme_content = await self._apply_middleware(
                "readme_fetch", readme_content
            )
            await bus.publish(
                Events.README_FETCHED,
                {"username": github_username, "length": len(readme_content)},
            )

        # Stage 1b: Fetch LinkedIn profile
        linkedin_data = {}
        if linkedin_url:
            linkedin_data = await fetch_linkedin_profile(linkedin_url)
            await bus.publish(
                Events.README_FETCHED, {"linkedin": True, "fields": len(linkedin_data)}
            )

        # Stage 1c: Fetch HuggingFace profile
        hf_data = {}
        if hf_username:
            hf_data = await fetch_huggingface_profile(hf_username)
            await bus.publish(
                Events.README_FETCHED,
                {"source": "huggingface", "fields": len(hf_data)},
            )

        # Stage 1d: Fetch ORCID profile
        orcid_data = {}
        if orcid_id:
            orcid_data = await fetch_orcid_profile(orcid_id)
            await bus.publish(
                Events.README_FETCHED, {"source": "orcid", "fields": len(orcid_data)}
            )

        # Stage 2: Build the prompt
        user_prompt = build_user_prompt(
            github_username,
            readme_content,
            additional_info,
            priority,
            resume_template,
            linkedin_data=linkedin_data,
            job_description=job_description,
            ats_feedback=ats_feedback,
            hf_data=hf_data,
            orcid_data=orcid_data,
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
    ):
        """Execute the pipeline with streaming generation. Yields tokens."""

        if demo:
            async for token in generate_resume_stream("", demo=True):
                yield token
            return

        # Stage 1: Fetch GitHub README
        readme_content = ""
        if github_username:
            readme_content = await fetch_github_readme(github_username)
            readme_content = await self._apply_middleware(
                "readme_fetch", readme_content
            )
            await bus.publish(
                Events.README_FETCHED,
                {"username": github_username, "length": len(readme_content)},
            )

        # Stage 1b: Fetch LinkedIn profile
        linkedin_data = {}
        if linkedin_url:
            linkedin_data = await fetch_linkedin_profile(linkedin_url)
            await bus.publish(
                Events.README_FETCHED, {"linkedin": True, "fields": len(linkedin_data)}
            )

        # Stage 1c: Fetch HuggingFace profile
        hf_data = {}
        if hf_username:
            hf_data = await fetch_huggingface_profile(hf_username)
            await bus.publish(
                Events.README_FETCHED,
                {"source": "huggingface", "fields": len(hf_data)},
            )

        # Stage 1d: Fetch ORCID profile
        orcid_data = {}
        if orcid_id:
            orcid_data = await fetch_orcid_profile(orcid_id)
            await bus.publish(
                Events.README_FETCHED, {"source": "orcid", "fields": len(orcid_data)}
            )

        # Stage 2: Build the prompt
        user_prompt = build_user_prompt(
            github_username,
            readme_content,
            additional_info,
            priority,
            resume_template,
            linkedin_data=linkedin_data,
            job_description=job_description,
            ats_feedback=ats_feedback,
            hf_data=hf_data,
            orcid_data=orcid_data,
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
