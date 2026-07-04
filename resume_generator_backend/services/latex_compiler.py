import os

import httpx

LATEX_SERVICE_URL = os.getenv("LATEX_SERVICE_URL", "http://latex-service:8000")


async def compile_latex_pdf(latex_content: str) -> bytes:
    if r"\documentclass" not in latex_content:
        latex_content = md_to_latex(latex_content)
    else:
        # strip anything before \documentclass (LLM sometimes prepends \begin{document})
        idx = latex_content.index(r"\documentclass")
        latex_content = latex_content[idx:]

    async with httpx.AsyncClient(timeout=310) as client:
        resp = await client.post(
            f"{LATEX_SERVICE_URL}/compile",
            json={"latex": latex_content},
        )

    if resp.status_code != 200:
        raise RuntimeError(f"LaTeX service error: {resp.text}")

    return resp.content


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
