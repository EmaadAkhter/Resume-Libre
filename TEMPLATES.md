# Contributing LaTeX Templates

Templates are the easiest way to contribute to Resume-Libre. A template is a **single `.tex` file** with `{{PLACEHOLDER}}` fields; the AI fills the placeholders with the user's real data and the Tectonic sidecar compiles the result to PDF.

Current templates live in [`templates/`](templates/). Open issues: [#12 AltaCV](https://github.com/EmaadAkhter/Resume-Libre/issues/12), [#13 Deedy](https://github.com/EmaadAkhter/Resume-Libre/issues/13), [#14 Friggeri](https://github.com/EmaadAkhter/Resume-Libre/issues/14).

## The rules

1. **One self-contained file.** The whole template is passed to the LLM and then to `tectonic` as a single input. No `\input`, no external `.cls`/`.sty` files.
2. **CTAN packages only.** Tectonic auto-downloads anything on CTAN (moderncv, xcolor, enumitem, fontawesome5, …). Custom classes like the real `awesome-cv.cls` or `deedy-resume.cls` are **not** on CTAN and will not compile — instead, recreate the *look* using the `article` class (see [`templates/awesome-style.tex`](templates/awesome-style.tex) for the pattern).
3. **Placeholders in double braces**, SCREAMING_SNAKE_CASE: `{{FIRST_NAME}}`, `{{JOB_TITLE}}`, `{{ACHIEVEMENT_1}}`. Use the same names as existing templates where possible — the AI knows them.
4. **Keep it small.** The template rides inside the LLM prompt; stay under ~120 lines. One example entry per section is enough — the AI repeats structures as needed.
5. **One page bias.** Tight margins, no `\vspace` extravagance. The product promises a one-page resume.

## Standard placeholder vocabulary

`FIRST_NAME` `LAST_NAME` `HEADLINE` `EMAIL` `PHONE` `LOCATION` `LINKEDIN_HANDLE` `GITHUB_HANDLE` `SUMMARY_2_LINES` — header/summary
`JOB_TITLE` `COMPANY` `DATES` `ACHIEVEMENT_1..3` — experience
`PROJECT_NAME` `PROJECT_URL` `PROJECT_DESCRIPTION` `PROJECT_TECH_STACK` — projects
`LANGUAGES` `FRAMEWORKS` `TOOLS` — skills
`DEGREE` `UNIVERSITY` `GRAD_YEAR` — education

## Verify before you PR

```bash
# 1. Fill placeholders with sample data (any values), then compile:
tectonic your-template-filled.tex

# Or compile against the exact production toolchain:
docker compose up -d latex-service
docker cp your-template-filled.tex resume-libre-latex-service-1:/tmp/
docker exec resume-libre-latex-service-1 sh -c "cd /tmp && tectonic your-template-filled.tex"
```

The PR checklist:

- [ ] `templates/<name>.tex` added, comment header crediting the design it's based on
- [ ] Compiles clean with Tectonic 0.15 (the sidecar image)
- [ ] Seed entry appended to `supabase/seed.sql` (use the `$tex$...$tex$` dollar-quoted form)
- [ ] Screenshot of the compiled PDF in the PR description

## How templates reach users

`supabase/seed.sql` inserts them as public rows in the `templates` table. Users can also upload private templates in-app (Template picker → upload `.tex`).
