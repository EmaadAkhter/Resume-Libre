-- ═══════════════════════════════════════════════════════
-- Seed Data — Default Templates
-- Run after all migrations are applied.
-- ═══════════════════════════════════════════════════════

-- 1. Public Markdown template (visible to all users)
INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Classic Markdown',
  'Standard ATS-friendly one-page resume in Markdown. Works with the live editor.',
  E'# {{NAME}}\n[{{EMAIL}}](mailto:{{EMAIL}}) | {{PHONE}} | {{LOCATION}} | [LinkedIn]({{LINKEDIN}}) | [GitHub]({{GITHUB}})\n\n## Experience\n\n**{{JOB_TITLE}}** | {{COMPANY}} | {{DATES}}\n- {{ACHIEVEMENT_1}}\n- {{ACHIEVEMENT_2}}\n- {{ACHIEVEMENT_3}}\n\n## Projects\n\n**{{PROJECT_NAME}}** | [Link]({{PROJECT_URL}})\n- {{DESCRIPTION}}\n- {{TECH_STACK}}\n\n## Skills\n\n**Languages:** {{LANGUAGES}}\n**Frameworks:** {{FRAMEWORKS}}\n**Tools:** {{TOOLS}}\n\n## Education\n\n**{{DEGREE}}** | {{UNIVERSITY}} | {{GRAD_YEAR}}\n',
  'md',
  false,
  true
)
ON CONFLICT DO NOTHING;

-- 2. Public LaTeX template (visible to all users)
INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Minimal LaTeX',
  'Clean one-page LaTeX resume using the article class. Compiles with Tectonic.',
  E'\\documentclass[11pt,a4paper]{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage[margin=0.5in]{geometry}\n\\usepackage{hyperref}\n\\usepackage{enumitem}\n\\usepackage{titlesec}\n\n\\titleformat{\\section}{\\large\\bfseries}{}{0em}{}\n\\titlespacing{\\section}{0pt}{8pt}{4pt}\n\\setlength{\\parindent}{0pt}\n\n\\begin{document}\n\n\\begin{center}\n  {\\Large \\bfseries {{NAME}}}\\\\[4pt]\n  \\href{mailto:{{EMAIL}}}{{{EMAIL}}} \\textbar\\ {{PHONE}} \\textbar\\ {{LOCATION}}\n  \\textbar\\ \\href{{{LINKEDIN}}}{LinkedIn} \\textbar\\ \\href{{{GITHUB}}}{GitHub}\n\\end{center}\n\n\\section*{Experience}\n\\textbf{{{JOB_TITLE}}} \\textbar\\ {{COMPANY}} \\textbar\\ {{DATES}}\n\\begin{itemize}[leftmargin=*,nosep]\n  \\item {{ACHIEVEMENT\\_1}}\n  \\item {{ACHIEVEMENT\\_2}}\n  \\item {{ACHIEVEMENT\\_3}}\n\\end{itemize}\n\n\\section*{Projects}\n\\textbf{{{PROJECT\\_NAME}}} \\textbar\\ \\href{{{PROJECT\\_URL}}}{Link}\n\\begin{itemize}[leftmargin=*,nosep]\n  \\item {{DESCRIPTION}}\n  \\item {{TECH\\_STACK}}\n\\end{itemize}\n\n\\section*{Skills}\n\\textbf{Languages:} {{LANGUAGES}}\\\\\n\\textbf{Frameworks:} {{FRAMEWORKS}}\\\\\n\\textbf{Tools:} {{TOOLS}}\n\n\\section*{Education}\n\\textbf{{{DEGREE}}} \\textbar\\ {{UNIVERSITY}} \\textbar\\ {{GRAD\\_YEAR}}\n\n\\end{document}\n',
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;

-- 3. Admin-only LaTeX template (only visible to admins)
INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Premium Two-Column LaTeX',
  'Admin-only: Two-column layout with sidebar for skills/contact. Advanced formatting.',
  E'\\documentclass[10pt,a4paper]{article}\n\\usepackage[utf8]{inputenc}\n\\usepackage[margin=0.4in,columnsep=0.3in]{geometry}\n\\usepackage{hyperref}\n\\usepackage{enumitem}\n\\usepackage{titlesec}\n\\usepackage{multicol}\n\n\\titleformat{\\section}{\\normalsize\\bfseries\\uppercase}{}{0em}{}\n\\titlespacing{\\section}{0pt}{6pt}{3pt}\n\\setlength{\\parindent}{0pt}\n\n\\begin{document}\n\n\\begin{center}\n  {\\Huge \\bfseries {{NAME}}}\\\\[2pt]\n  \\small \\href{mailto:{{EMAIL}}}{{{EMAIL}}} \\textbar\\ {{PHONE}} \\textbar\\ {{LOCATION}}\n\\end{center}\n\n\\hrule\n\n\\begin{multicols}{2}\n\n\\section*{Skills}\n\\textbf{Languages:} {{LANGUAGES}}\\\\\n\\textbf{Frameworks:} {{FRAMEWORKS}}\\\\\n\\textbf{Tools:} {{TOOLS}}\n\n\\section*{Education}\n\\textbf{{{DEGREE}}}\\\\\n{{UNIVERSITY}} \\\\ {{GRAD\\_YEAR}}\n\n\\columnbreak\n\n\\section*{Experience}\n\\textbf{{{JOB\\_TITLE}}} \\hfill {{DATES}}\\\\\n{{COMPANY}}\n\\begin{itemize}[leftmargin=*,nosep]\n  \\item {{ACHIEVEMENT\\_1}}\n  \\item {{ACHIEVEMENT\\_2}}\n\\end{itemize}\n\n\\section*{Projects}\n\\textbf{{{PROJECT\\_NAME}}}\n\\begin{itemize}[leftmargin=*,nosep]\n  \\item {{DESCRIPTION}}\n\\end{itemize}\n\n\\end{multicols}\n\n\\end{document}\n',
  'tex',
  true,
  false
)
ON CONFLICT DO NOTHING;

-- 4+5. Community LaTeX templates (see templates/ directory + TEMPLATES.md)

INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Awesome Style',
  'Awesome-CV-inspired single-column layout with skyblue accents. Compiles with Tectonic (CTAN packages only).',
  $tex$% Awesome-style — Awesome-CV-inspired look built on the article class so it
% compiles with Tectonic from CTAN packages alone (the real awesome-cv.cls is
% not on CTAN). Skyblue accent, rule-under sections, tight one-page layout.
% Placeholders in {{DOUBLE_BRACES}} are filled by the AI with the user's data.
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.55in]{geometry}
\usepackage[dvipsnames]{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}

\definecolor{awesome}{HTML}{0395DE}
\definecolor{darktext}{HTML}{414141}

\titleformat{\section}{\large\bfseries\color{darktext}}{}{0em}{}[{\color{awesome}\titlerule[1.2pt]}]
\titlespacing{\section}{0pt}{10pt}{6pt}
\setlength{\parindent}{0pt}
\pagestyle{empty}

\begin{document}

\begin{center}
  {\Huge {{FIRST_NAME}} {\bfseries\color{awesome}{{LAST_NAME}}}}\\[4pt]
  {\small\color{darktext} {{HEADLINE}}}\\[6pt]
  {\footnotesize
    \href{mailto:{{EMAIL}}}{{{EMAIL}}} \textbar\
    {{PHONE}} \textbar\ {{LOCATION}} \textbar\
    \href{https://linkedin.com/in/{{LINKEDIN_HANDLE}}}{linkedin.com/in/{{LINKEDIN_HANDLE}}} \textbar\
    \href{https://github.com/{{GITHUB_HANDLE}}}{github.com/{{GITHUB_HANDLE}}}}
\end{center}

\section{Summary}
{{SUMMARY_2_LINES}}

\section{Experience}
\textbf{{{JOB_TITLE}}} \hfill {\color{awesome}\small {{DATES}}}\\
{\small\itshape {{COMPANY}} — {{LOCATION}}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{ACHIEVEMENT_1}}
  \item {{ACHIEVEMENT_2}}
  \item {{ACHIEVEMENT_3}}
\end{itemize}

\section{Projects}
\textbf{{{PROJECT_NAME}}} \hfill {\color{awesome}\small \href{{{PROJECT_URL}}}{link}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{PROJECT_DESCRIPTION}}
  \item {{PROJECT_TECH_STACK}}
\end{itemize}

\section{Skills}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item \textbf{Languages:} {{LANGUAGES}}
  \item \textbf{Frameworks:} {{FRAMEWORKS}}
  \item \textbf{Tools:} {{TOOLS}}
\end{itemize}

\section{Education}
\textbf{{{DEGREE}}} \hfill {\color{awesome}\small {{GRAD_YEAR}}}\\
{\small\itshape {{UNIVERSITY}}}

\end{document}
$tex$,
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;

INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'ModernCV Classic',
  'The classic moderncv class from CTAN — timeless two-tone resume. Compiles with Tectonic.',
  $tex$% ModernCV Classic — real moderncv class from CTAN, compiles with Tectonic.
% Placeholders in {{DOUBLE_BRACES}} are filled by the AI with the user's data.
\documentclass[10pt,a4paper,sans]{moderncv}
\moderncvstyle{classic}
\moderncvcolor{blue}
\usepackage[scale=0.82]{geometry}

\name{{{FIRST_NAME}}}{{{LAST_NAME}}}
\title{{{HEADLINE}}}
\phone[mobile]{{{PHONE}}}
\email{{{EMAIL}}}
\social[linkedin]{{{LINKEDIN_HANDLE}}}
\social[github]{{{GITHUB_HANDLE}}}

\begin{document}

\makecvtitle

\section{Summary}
\cvitem{}{{{SUMMARY_2_LINES}}}

\section{Experience}
\cventry{{{DATES}}}{{{JOB_TITLE}}}{{{COMPANY}}}{{{LOCATION}}}{}{%
\begin{itemize}
\item {{ACHIEVEMENT_1}}
\item {{ACHIEVEMENT_2}}
\item {{ACHIEVEMENT_3}}
\end{itemize}}

\section{Projects}
\cventry{}{{{PROJECT_NAME}}}{}{}{}{%
\begin{itemize}
\item {{PROJECT_DESCRIPTION}}
\item {{PROJECT_TECH_STACK}}
\end{itemize}}

\section{Skills}
\cvitem{Languages}{{{LANGUAGES}}}
\cvitem{Frameworks}{{{FRAMEWORKS}}}
\cvitem{Tools}{{{TOOLS}}}

\section{Education}
\cventry{{{GRAD_YEAR}}}{{{DEGREE}}}{{{UNIVERSITY}}}{}{}{}

\end{document}
$tex$,
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;
