from services.export_utils import (
    parse_markdown_line,
    get_filename_base,
    markdown_to_pdf,
    markdown_to_docx,
)


def test_parse_markdown_line_plain_text():
    parts = parse_markdown_line("hello world")
    assert len(parts) == 1
    assert parts[0] == ("normal", "hello world")


def test_parse_markdown_line_bold():
    parts = parse_markdown_line("**bold text**")
    assert len(parts) == 1
    assert parts[0] == ("bold", "bold text")


def test_parse_markdown_line_link():
    parts = parse_markdown_line("[click](https://example.com)")
    assert len(parts) == 1
    assert parts[0][0] == "link"
    assert parts[0][1] == "click"
    assert parts[0][2] == "https://example.com"


def test_parse_markdown_line_mixed():
    parts = parse_markdown_line("hello **world** and [link](url)")
    assert len(parts) == 4
    assert parts[0] == ("normal", "hello ")
    assert parts[1] == ("bold", "world")
    assert parts[2] == ("normal", " and ")
    assert parts[3][0] == "link"


def test_get_filename_base_extracts_name():
    md = "# John Doe\n## Experience\n..."
    assert get_filename_base(md) == "John_Doe"


def test_get_filename_base_no_heading():
    md = "Just some text without a heading"
    assert get_filename_base(md) == "resume"


def test_markdown_to_pdf_returns_bytes(sample_resume_md):
    pdf_bytes = markdown_to_pdf(sample_resume_md)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:4] == b"%PDF"


def test_markdown_to_docx_returns_buffer(sample_resume_md):
    buffer = markdown_to_docx(sample_resume_md)
    assert buffer is not None
    # DOCX files start with PK (zip)
    buffer.seek(0)
    assert buffer.read(2) == b"PK"
