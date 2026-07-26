<div align="center">

<img src="resume-generator-frontend/public/logo.png" alt="Resume-Libre" width="400"/>

**Open-source AI resume generator: your GitHub profile, LinkedIn, and a job description in — a polished, one-page LaTeX PDF out.**

[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Made with React](https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=for-the-badge&logo=react)](https://react.dev)

</div>

---

## What is Resume-Libre?

Resume-Libre reads your **GitHub profile README**, takes your **LinkedIn profile** (paste the text, or let the server scrape it), combines that with any extra information and a **job description** you provide, and uses an LLM (via OpenRouter) to write a complete **LaTeX document** — compiled to a real PDF by [Tectonic](https://tectonic-typesetting.github.io/) and streamed into the editor token by token.

No fake "ATS score". No web-page-pretending-to-be-a-PDF. Real typesetting, tailored to the role.

## Features

| Feature | Details |
| --- | --- |
| **AI generation** | Any LLM via OpenRouter (configurable model), streamed via SSE |
| **GitHub integration** | Fetches your profile README as raw material |
| **LinkedIn input** | Paste your profile text (default, no scraping), or configure Apify scraping |
| **Job targeting** | Feed in a job description — the LLM aligns your experience to it |
| **Resume upload** | Extracts text from existing PDF/DOCX/TXT resumes, in memory only |
| **LaTeX pipeline** | LLM emits a complete LaTeX document; Tectonic compiles the PDF |
| **Export** | PDF and LaTeX source |
| **Version control** | Branch, commit, and roll back resumes — like git for resumes |
| **Templates** | Save and reuse `.tex` templates; admin-curated public library |
| **Auth & privacy** | Supabase auth, row-level security, uploads never written to disk |
| **Self-hostable** | Docker Compose for dev and production (Caddy + auto-TLS) |

## Quickstart (self-host)

```bash
git clone https://github.com/EmaadAkhter/Resume-Libre.git
cd Resume-Libre
cp .env.example .env   # fill in OpenRouter + Supabase keys
docker compose up
```

Frontend at http://localhost:3000, API at http://localhost:8000.

You need:
- A free [OpenRouter](https://openrouter.ai/keys) API key (free models work — default is `openai/gpt-oss-120b:free`)
- A free [Supabase](https://supabase.com) project (run the SQL in `supabase/migrations/` in order)
- Optionally an [Apify](https://apify.com) token for LinkedIn URL scraping — skip it and use paste-text input

## Architecture

```
┌──────────────┐     ┌───────────────────┐     ┌────────────────┐
│  React 19 /  │────▶│  FastAPI backend  │────▶│  OpenRouter    │
│  Vite + TW   │ SSE │  (generation,     │     │  (LLM)         │
└──────┬───────┘     │  export, auth)    │     └────────────────┘
       │             └───────┬───────────┘
       │ direct CRUD         │ HTTP           ┌────────────────┐
       ▼                     ├───────────────▶│ LaTeX sidecar  │
┌──────────────┐             │                │ (Tectonic)     │
│   Supabase   │             ▼                └────────────────┘
│ (auth + DB + │     ┌────────────────┐
│  storage)    │     │     Redis      │
└──────────────┘     │ (cache + rate  │
                     │    limits)     │
                     └────────────────┘
```

- **Frontend** (`resume-generator-frontend/`): React 19, Vite, Tailwind. Talks to Supabase directly for resume/version CRUD, and to the backend for generation/export.
- **Backend** (`resume_generator_backend/`): FastAPI. Fetches GitHub/LinkedIn data, builds the prompt, streams LLM output, compiles LaTeX via the sidecar. JWT-protected, Redis-backed rate limits.
- **LaTeX sidecar** (`latex-service/`): tiny FastAPI service wrapping the Tectonic binary — keeps the heavyweight LaTeX toolchain out of the main API image.
- **Supabase** (`supabase/migrations/`): auth, Postgres with row-level security, storage buckets.

## Environment variables

See [.env.example](.env.example) for the full annotated list. The essentials:

| Variable | Purpose |
| --- | --- |
| `OPENROUTER_API_KEY` | LLM access (required) |
| `OPENROUTER_MODEL` | Model id, default `openai/gpt-oss-120b:free` |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` | Auth + database |
| `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` / `VITE_API_URL` | Frontend build |
| `APIFY_API_TOKEN` | Optional — LinkedIn URL scraping |
| `REDIS_URL` | Cache + rate-limit counters (set automatically in compose) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins for production |

## Development

```bash
# Backend
cd resume_generator_backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest                       # run tests
uvicorn main:app --reload

# Frontend
cd resume-generator-frontend
npm install
npm run dev                  # Vite dev server
npx vitest run               # tests
```

CI runs ruff, pytest, eslint, vitest, and a production build on every push. Pre-commit hooks (`pre-commit install`) mirror the same checks.

## Privacy

Uploaded files are processed **in memory and never written to disk**. Resume content is never used for anything beyond your own request. Full policy: [PRIVACY.md](PRIVACY.md) · [TERMS.md](TERMS.md)

## Contributing

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Good first issues: LaTeX resume templates ([#12](https://github.com/EmaadAkhter/Resume-Libre/issues/12)–[#14](https://github.com/EmaadAkhter/Resume-Libre/issues/14)), and the wired-but-unrouted Fresher Wizard ([#3](https://github.com/EmaadAkhter/Resume-Libre/issues/3)).

## License

AGPL-3.0 — see [LICENSE](LICENSE).

Why AGPL? Resume-Libre is and will stay open source. AGPL keeps it that way: use it, fork it, self-host it freely — but if you run a modified version as a service, share your changes back. Code published before the license change (through commit `dee7144`) remains available under MIT.

---

<div align="center">

Built by [Emaad Ansari](https://github.com/EmaadAkhter) · Powered by OpenRouter

**If this saved you an hour of resume formatting, drop a star**

</div>
