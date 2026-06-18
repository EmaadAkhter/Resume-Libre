import asyncio
import os
import subprocess
import tempfile
from pathlib import Path


def md_to_latex(markdown: str) -> str:
    """Convert a Markdown resume to LaTeX.

    Handles: # / ## headers, bold, bullet lists, links, inline separators.
    ponytail: regex-based converter, use pandoc if conversion gets complex.
    """
    lines = markdown.strip().split("\n")
    latex = [
        "\\documentclass[11pt,a4paper]{article}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage[margin=0.5in]{geometry}",
        "\\usepackage{hyperref}",
        "\\usepackage{enumitem}",
        "\\usepackage{titlesec}",
        "\\titleformat{\\section}{\\large\\bfseries}{}{0em}{}",
        "\\titlespacing{\\section}{0pt}{8pt}{4pt}",
        "\\setlength{\\parindent}{0pt}",
        "\\begin{document}",
        "",
    ]

    in_itemize = False

    for line in lines:
        line = line.strip()

        if not line:
            if in_itemize:
                latex.append("\\end{itemize}")
                in_itemize = False
            latex.append("")
            continue

        if line.startswith("# ") and not in_itemize:
            text = _md_inline_to_latex(line[2:])
            latex.append(f"\\begin{{center}}\\Large \\bfseries {text}\\end{{center}}")

        elif line.startswith("## "):
            if in_itemize:
                latex.append("\\end{itemize}")
                in_itemize = False
            text = _md_inline_to_latex(line[3:])
            latex.append(f"\\section*{{{text}}}")

        elif line.startswith("- ") or line.startswith("* "):
            if not in_itemize:
                latex.append("\\begin{itemize}[leftmargin=*,nosep]")
                in_itemize = True
            text = _md_inline_to_latex(line[2:])
            latex.append(f"  \\item {text}")

        else:
            if in_itemize:
                latex.append("\\end{itemize}")
                in_itemize = False
            text = _md_inline_to_latex(line)
            latex.append(text + "\\\\")

    if in_itemize:
        latex.append("\\end{itemize}")

    latex.append("")
    latex.append("\\end{document}")
    return "\n".join(latex)


def _md_inline_to_latex(text: str) -> str:
    import re

    text = text.replace("&", "\\&")
    text = text.replace("%", "\\%")
    text = text.replace("_", "\\_")
    text = text.replace("#", "\\#")

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\\href{\2}{\1}", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)

    return text


async def compile_latex_pdf(latex_content: str) -> bytes:
    """Compile LaTeX to PDF using Tectonic (runs in thread pool to avoid
    blocking the event loop)."""
    tectonic_path = os.getenv("TECTONIC_PATH", "tectonic")

    loop = asyncio.get_event_loop()

    def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = Path(tmpdir) / "resume.tex"
            pdf_path = Path(tmpdir) / "resume.pdf"

            tex_path.write_text(latex_content, encoding="utf-8")

            result = subprocess.run(
                [tectonic_path, str(tex_path), "--outdir", tmpdir],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Tectonic compilation failed: {result.stderr[:500]}"
                )

            if not pdf_path.exists():
                raise RuntimeError("Tectonic did not produce a PDF file")

            return pdf_path.read_bytes()

    return await loop.run_in_executor(None, _run)
