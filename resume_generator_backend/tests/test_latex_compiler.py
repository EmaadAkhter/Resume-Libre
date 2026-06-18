from services.latex_compiler import md_to_latex


def test_md_to_latex_basic_structure():
    latex = md_to_latex("# John\n## Section\nContent here")
    assert "\\documentclass" in latex
    assert "\\begin{document}" in latex
    assert "\\end{document}" in latex


def test_md_to_latex_converts_headers():
    latex = md_to_latex("# Name")
    assert "Name" in latex
    assert "\\begin{center}" in latex


def test_md_to_latex_converts_section():
    latex = md_to_latex("## Experience")
    assert "\\section*{Experience}" in latex


def test_md_to_latex_converts_bullets():
    latex = md_to_latex("- Item one\n- Item two")
    assert "\\begin{itemize}" in latex
    assert "\\item Item one" in latex
    assert "\\item Item two" in latex
    assert "\\end{itemize}" in latex


def test_md_to_latex_escapes_special_chars():
    latex = md_to_latex("100% accuracy & more")
    assert "\\%" in latex
    assert "\\&" in latex


def test_md_to_latex_converts_bold():
    latex = md_to_latex("**bold text**")
    assert "\\textbf{bold text}" in latex


def test_md_to_latex_converts_links():
    latex = md_to_latex("[click](https://example.com)")
    assert "\\href{https://example.com}{click}" in latex
