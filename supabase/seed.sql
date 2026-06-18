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
