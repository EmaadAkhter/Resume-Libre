# Architecture

Four containers (see `docker-compose.yml` / `docker-compose.prod.yml`):

```
                                ┌─────────────────────────┐
   browser ──────────────────▶  │  frontend               │
      │                         │  React 19 + Vite + TW   │
      │  auth, resume CRUD      │  (nginx in prod)        │
      ▼                         └───────────┬─────────────┘
┌──────────────┐                            │ /api/* (JWT)
│   Supabase   │      verify JWT            ▼
│  auth + PG   │ ◀──────────────┌─────────────────────────┐
│  + storage   │                │  backend (FastAPI)      │
└──────────────┘                │  generation / export /  │
                                │  extract / health       │
                                └──┬──────────┬───────────┘
                                   │          │
                     OpenRouter ◀──┘          ├──▶ latex-service (Tectonic)
                     (LLM, SSE)               └──▶ redis (cache + rate limits)
```

## Request flow: generating a resume

1. Frontend collects GitHub username, LinkedIn (pasted text or URL), extra info, job description, template.
2. `GET /generate-resume-stream` (SSE) with the Supabase JWT in `Authorization`.
3. Backend (`services/pipeline.py`): fetch GitHub README (Redis-cached 1h) → optionally scrape LinkedIn via Apify (cached 24h) → build prompt (`services/prompt.py`) → stream LLM tokens from OpenRouter (`services/genrate_resume.py`).
4. Tokens stream to the editor. On completion the frontend POSTs the LaTeX to `/export-resume` (`format: latex_pdf`); backend forwards to the **latex-service** sidecar (`POST /compile`), Tectonic compiles, PDF renders in an iframe.
5. Versions/branches are saved by the frontend **directly to Supabase** (RLS-enforced) — the backend is stateless with respect to resume storage.

## Key decisions

- **LaTeX-only pipeline** — the LLM emits a complete `\documentclass...\end{document}` document. No Markdown intermediate (removed; it produced weaker PDFs).
- **Tectonic in a sidecar** — the LaTeX toolchain is heavy; isolating it keeps the API image slim and lets it be memory-capped independently (600 MB in prod).
- **Frontend ↔ Supabase direct** for CRUD — RLS is the authorization layer; the backend only handles compute (LLM, PDF, parsing) and verifies JWTs for those.
- **Demo mode** — `DEMO_MODE=true` serves a canned LaTeX fixture (still compiled for real); `ALLOW_DEMO_REQUESTS=true` lets production serve the demo to anonymous visitors at zero LLM cost.
- **Rate limits in Redis** — shared across uvicorn workers, survive restarts; keyed by user id when authenticated, IP otherwise.

## Directory map

| Path | What |
|---|---|
| `resume_generator_backend/core/` | app factory, auth deps, limiter, logging |
| `resume_generator_backend/routers/` | health, generation, export, debug (SSE event firehose) |
| `resume_generator_backend/services/` | pipeline, prompt, LLM client, GitHub/LinkedIn fetchers, LaTeX compile client, Redis cache |
| `resume_generator_backend/fixtures/` | canned demo output |
| `latex-service/` | 40-line FastAPI wrapper around the Tectonic binary |
| `resume-generator-frontend/src/` | pages, components, hooks, lib (see its README) |
| `supabase/migrations/` | schema, RLS policies, storage buckets (apply in order) |
| `templates/` | contributed LaTeX resume templates (see TEMPLATES.md) |
