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

-- 6-8. Community LaTeX templates (see templates/ directory + TEMPLATES.md)

INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'AltaCV Style',
  'AltaCV-inspired layout with accent headings and two-column skills block. Compiles with Tectonic (CTAN packages only).',
  $tex$% AltaCV-style — inspired by LianTze Lim's AltaCV look (accent-colored
% headings, sidebar-feel via a two-column skills block) rebuilt on the
% article class: the real altacv.cls is not on CTAN so it cannot compile
% under Tectonic as a single file.
% Placeholders in {{DOUBLE_BRACES}} are filled by the AI with the user's data.
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{paracol}

\definecolor{accent}{HTML}{AA0000}
\definecolor{body}{HTML}{444444}

\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[{\color{accent}\titlerule[0.8pt]}]
\titlespacing{\section}{0pt}{8pt}{5pt}
\setlength{\parindent}{0pt}
\color{body}
\pagestyle{empty}

\begin{document}

{\Huge\bfseries\color{accent} {{FIRST_NAME}} {{LAST_NAME}}}\\[3pt]
{\large {{HEADLINE}}}\\[5pt]
{\footnotesize
  \href{mailto:{{EMAIL}}}{{{EMAIL}}} \,\textbullet\,
  {{PHONE}} \,\textbullet\, {{LOCATION}} \,\textbullet\,
  \href{https://linkedin.com/in/{{LINKEDIN_HANDLE}}}{in/{{LINKEDIN_HANDLE}}} \,\textbullet\,
  \href{https://github.com/{{GITHUB_HANDLE}}}{gh/{{GITHUB_HANDLE}}}}

\vspace{4pt}

\section{Summary}
{{SUMMARY_2_LINES}}

\section{Experience}
\textbf{{{JOB_TITLE}}} \hfill {\color{accent}\small {{DATES}}}\\
{\small\itshape {{COMPANY}} — {{LOCATION}}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{ACHIEVEMENT_1}}
  \item {{ACHIEVEMENT_2}}
  \item {{ACHIEVEMENT_3}}
\end{itemize}

\section{Projects}
\textbf{{{PROJECT_NAME}}} \hfill {\color{accent}\small \href{{{PROJECT_URL}}}{link}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{PROJECT_DESCRIPTION}}
  \item {{PROJECT_TECH_STACK}}
\end{itemize}

\columnratio{0.5}
\begin{paracol}{2}
\section{Skills}
\textbf{Languages:} {{LANGUAGES}}\\
\textbf{Frameworks:} {{FRAMEWORKS}}\\
\textbf{Tools:} {{TOOLS}}
\switchcolumn
\section{Education}
\textbf{{{DEGREE}}} \hfill {\color{accent}\small {{GRAD_YEAR}}}\\
{\small\itshape {{UNIVERSITY}}}
\end{paracol}

\end{document}
$tex$,
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;

INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Deedy Style',
  'Deedy-Resume-inspired two-column layout (skills/education sidebar). Compiles with Tectonic.',
  $tex$% Deedy-style — inspired by Debarghya Das's Deedy-Resume two-column look,
% rebuilt on the article class with paracol: deedy-resume.cls is not on
% CTAN so it cannot compile under Tectonic as a single file.
% Placeholders in {{DOUBLE_BRACES}} are filled by the AI with the user's data.
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.5in]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{paracol}

\definecolor{deedyblue}{HTML}{2C6FBB}
\definecolor{gray}{HTML}{5C5C5C}

\titleformat{\section}{\normalsize\bfseries\color{deedyblue}}{}{0em}{\MakeUppercase}[{\titlerule[0.6pt]}]
\titlespacing{\section}{0pt}{8pt}{4pt}
\setlength{\parindent}{0pt}
\pagestyle{empty}

\begin{document}

\begin{center}
  {\Huge {{FIRST_NAME}} {\bfseries\color{deedyblue}{{LAST_NAME}}}}\\[3pt]
  {\small\color{gray} {{HEADLINE}}}\\[4pt]
  {\footnotesize
    \href{mailto:{{EMAIL}}}{{{EMAIL}}} | {{PHONE}} | {{LOCATION}} |
    \href{https://linkedin.com/in/{{LINKEDIN_HANDLE}}}{in/{{LINKEDIN_HANDLE}}} |
    \href{https://github.com/{{GITHUB_HANDLE}}}{gh/{{GITHUB_HANDLE}}}}
\end{center}

\columnratio{0.33}
\begin{paracol}{2}

% ─── Left column ───
\section{Skills}
\textbf{Languages}\\ {{LANGUAGES}}\\[4pt]
\textbf{Frameworks}\\ {{FRAMEWORKS}}\\[4pt]
\textbf{Tools}\\ {{TOOLS}}

\section{Education}
\textbf{{{UNIVERSITY}}}\\
{\small {{DEGREE}}}\\
{\small\color{gray} {{GRAD_YEAR}}}

\section{Links}
\href{https://github.com/{{GITHUB_HANDLE}}}{github.com/{{GITHUB_HANDLE}}}\\
\href{https://linkedin.com/in/{{LINKEDIN_HANDLE}}}{linkedin.com/in/{{LINKEDIN_HANDLE}}}

\switchcolumn

% ─── Right column ───
\section{Summary}
{{SUMMARY_2_LINES}}

\section{Experience}
\textbf{{{COMPANY}}} \textbar\ {{JOB_TITLE}} \hfill {\color{gray}\small {{DATES}}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{ACHIEVEMENT_1}}
  \item {{ACHIEVEMENT_2}}
  \item {{ACHIEVEMENT_3}}
\end{itemize}

\section{Projects}
\textbf{{{PROJECT_NAME}}} \hfill {\color{gray}\small \href{{{PROJECT_URL}}}{link}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{PROJECT_DESCRIPTION}}
  \item {{PROJECT_TECH_STACK}}
\end{itemize}

\end{paracol}

\end{document}
$tex$,
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;

INSERT INTO templates (name, description, content, format, is_admin_only, is_public)
VALUES (
  'Friggeri Style',
  'Friggeri-CV-inspired design with header band and two-tone section titles. Compiles with Tectonic.',
  $tex$% Friggeri-style — inspired by Adrien Friggeri's CV (bold header band,
% gray/accent section titles) rebuilt on the article class: the real
% friggeri-cv.cls needs XeLaTeX-only fonts and is not on CTAN.
% Placeholders in {{DOUBLE_BRACES}} are filled by the AI with the user's data.
\documentclass[10pt,a4paper]{article}
\usepackage[margin=0.55in]{geometry}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}

\definecolor{fgray}{HTML}{4D4D4D}
\definecolor{faccent}{HTML}{D44424}
\definecolor{fband}{HTML}{F5F5F5}

% Friggeri signature: gray word + accent word section titles handled by
% \fsection{gray}{accent}
\newcommand{\fsection}[2]{%
  \vspace{8pt}{\large {\color{fgray}\bfseries #1}{\color{faccent}\bfseries #2}}\\[-8pt]
  {\color{fgray}\rule{\linewidth}{0.6pt}}\\[2pt]}
\setlength{\parindent}{0pt}
\pagestyle{empty}

\begin{document}

\begin{center}
  \colorbox{fband}{\parbox{\dimexpr\linewidth-2\fboxsep}{\centering
    \vspace{6pt}
    {\Huge {\color{fgray}{{FIRST_NAME}}} {\color{faccent}\bfseries {{LAST_NAME}}}}\\[4pt]
    {\small\color{fgray} {{HEADLINE}}}\\[4pt]
    {\footnotesize
      \href{mailto:{{EMAIL}}}{{{EMAIL}}} \textbullet\ {{PHONE}} \textbullet\ {{LOCATION}} \textbullet\
      \href{https://linkedin.com/in/{{LINKEDIN_HANDLE}}}{in/{{LINKEDIN_HANDLE}}} \textbullet\
      \href{https://github.com/{{GITHUB_HANDLE}}}{gh/{{GITHUB_HANDLE}}}}
    \vspace{6pt}}}
\end{center}

\fsection{Sum}{mary}
{{SUMMARY_2_LINES}}

\fsection{Exper}{ience}
\textbf{{{JOB_TITLE}}} \textbar\ {{COMPANY}} \hfill {\color{faccent}\small {{DATES}}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{ACHIEVEMENT_1}}
  \item {{ACHIEVEMENT_2}}
  \item {{ACHIEVEMENT_3}}
\end{itemize}

\fsection{Pro}{jects}
\textbf{{{PROJECT_NAME}}} \hfill {\color{faccent}\small \href{{{PROJECT_URL}}}{link}}
\begin{itemize}[leftmargin=*,nosep,itemsep=2pt]
  \item {{PROJECT_DESCRIPTION}}
  \item {{PROJECT_TECH_STACK}}
\end{itemize}

\fsection{Sk}{ills}
\textbf{Languages:} {{LANGUAGES}}\\
\textbf{Frameworks:} {{FRAMEWORKS}}\\
\textbf{Tools:} {{TOOLS}}

\fsection{Educ}{ation}
\textbf{{{DEGREE}}} \textbar\ {{UNIVERSITY}} \hfill {\color{faccent}\small {{GRAD_YEAR}}}

\end{document}
$tex$,
  'tex',
  false,
  true
)
ON CONFLICT DO NOTHING;
