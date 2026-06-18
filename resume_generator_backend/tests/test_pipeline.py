import pytest
from services.pipeline import ResumePipeline


@pytest.fixture
def pipeline():
    return ResumePipeline()


def test_pipeline_has_middleware_hooks(pipeline):
    assert "readme_fetch" in pipeline._middleware
    assert "prompt_build" in pipeline._middleware
    assert "generation" in pipeline._middleware
    assert "validation" in pipeline._middleware


def test_pipeline_on_readme_fetch_adds_middleware(pipeline):
    def my_middleware(data):
        return data

    pipeline.on_readme_fetch(my_middleware)
    assert my_middleware in pipeline._middleware["readme_fetch"]


def test_pipeline_on_prompt_build_adds_middleware(pipeline):
    def my_middleware(data):
        return data

    pipeline.on_prompt_build(my_middleware)
    assert my_middleware in pipeline._middleware["prompt_build"]


def test_pipeline_apply_middleware_transforms_data(pipeline):
    import asyncio

    def upper(data):
        return data.upper()

    pipeline.on_prompt_build(upper)
    result = asyncio.run(pipeline._apply_middleware("prompt_build", "hello"))
    assert result == "HELLO"


def test_pipeline_apply_middleware_chained(pipeline):
    import asyncio

    def add_a(data):
        return data + "a"

    def add_b(data):
        return data + "b"

    pipeline.on_prompt_build(add_a)
    pipeline.on_prompt_build(add_b)
    result = asyncio.run(pipeline._apply_middleware("prompt_build", ""))
    assert result == "ab"
