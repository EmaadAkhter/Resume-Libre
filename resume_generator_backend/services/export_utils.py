import re

from .latex_compiler import compile_latex_pdf, md_to_latex


async def latex_to_pdf(latex_content: str) -> bytes:
    """Compile LaTeX to PDF using Tectonic."""
    return await compile_latex_pdf(latex_content)


async def markdown_to_latex_pdf(markdown_text: str) -> bytes:
    """Convert Markdown to LaTeX, then compile to PDF via Tectonic."""
    latex = md_to_latex(markdown_text)
    return await compile_latex_pdf(latex)


def get_filename_base(markdown_text: str) -> str:
    lines = markdown_text.split("\n")
    for line in lines:
        if line.startswith("# "):
            name = line[2:].strip()

            name = re.sub(r"[^\w\s-]", "", name)
            name = re.sub(r"[-\s]+", "_", name)
            return name
    return "resume"
