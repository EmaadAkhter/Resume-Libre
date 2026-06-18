from services.clean_up import (
    clean_markdown_output,
    validate_and_fix_format,
    validate_resume_quality,
)


def test_clean_markdown_output_strips_code_fences():
    text = "```markdown\n# Hello\n```"
    result = clean_markdown_output(text)
    assert "```" not in result
    assert "# Hello" in result


def test_clean_markdown_output_strips_emoji():
    text = "Hello 🚀 World"
    result = clean_markdown_output(text)
    assert "🚀" not in result
    assert "Hello" in result
    assert "World" in result


def test_clean_markdown_output_collapses_extra_spaces():
    text = "Hello    World"
    result = clean_markdown_output(text)
    assert "  " not in result


def test_validate_and_fix_format_adds_blank_before_headers():
    text = "Some text\n## Header\nMore text"
    result = validate_and_fix_format(text)
    lines = result.split("\n")
    idx = lines.index("## Header")
    assert lines[idx - 1] == ""


def test_validate_resume_quality_detects_html():
    text = "# Resume\n<div>content</div>"
    result = validate_resume_quality(text)
    assert not result["valid"]
    assert any("HTML" in issue for issue in result["issues"])


def test_validate_resume_quality_detects_generic_phrases():
    text = "# Resume\nI am passionate about building applications"
    result = validate_resume_quality(text)
    assert any("passionate" in w for w in result["warnings"])


def test_validate_resume_quality_passes_clean_resume(sample_resume_md):
    result = validate_resume_quality(sample_resume_md)
    assert result["valid"]
    assert result["line_count"] > 0
