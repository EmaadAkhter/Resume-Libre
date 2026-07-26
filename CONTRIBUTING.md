# Contributing to Resume-Libre

Thanks for your interest in contributing! This guide will get you set up and shipping code fast.

## Prerequisites

- **Node.js 20+** — [download](https://nodejs.org/)
- **Python 3.11+** — [download](https://www.python.org/downloads/)
- **Docker** + **Docker Compose** — [download](https://docs.docker.com/get-docker/)
- **Tectonic** (LaTeX engine) — `curl -fsSL https://drop-sh.fullyjustified.net | sh` (macOS/Linux) or see [releases](https://github.com/tectonic-typesetting/tectonic/releases)
- An [OpenRouter](https://openrouter.ai/keys) API key (free tier works) — *not needed for demo mode*
- A [Supabase](https://supabase.com) project (free tier works) — *not needed for demo mode*

## Quick Start — zero keys (demo mode)

The fastest dev loop. No API keys, no Supabase project:

```bash
git clone https://github.com/EmaadAkhter/Resume-Libre.git
cd Resume-Libre
echo "DEMO_MODE=true" > .env
docker compose up --build
```

Open http://localhost:3000/demo — generation streams a canned resume and Tectonic compiles a real PDF. Perfect for working on UI, templates, export, or the LaTeX pipeline.

## Quick Start — full stack

```bash
cp .env.example .env
# Edit .env with your OpenRouter + Supabase keys
docker compose up --build
```

- Frontend → http://localhost:3000
- Backend → http://localhost:8000/docs

## Quick Start (Manual)

### Backend

```bash
cd resume_generator_backend
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd resume-generator-frontend
npm install
npm run dev
```

## Project Structure

```
Resume-Libre/
├── resume_generator_backend/     # FastAPI — AI generation, LaTeX compile, API
├── resume-generator-frontend/    # Vite + React 19 — UI, auth, editor
├── supabase/                     # Migrations, RLS policies, seed data
├── docker-compose.yml            # Dev orchestration
└── .github/                      # CI/CD, issue/PR templates
```

## Good First Contributions

- **LaTeX templates** — the friendliest entry point. See [TEMPLATES.md](TEMPLATES.md); open template issues: [#12](https://github.com/EmaadAkhter/Resume-Libre/issues/12), [#13](https://github.com/EmaadAkhter/Resume-Libre/issues/13), [#14](https://github.com/EmaadAkhter/Resume-Libre/issues/14)
- **Fresher Wizard** ([#3](https://github.com/EmaadAkhter/Resume-Libre/issues/3)) — the component exists (`FresherWizard.jsx`), it needs routing and intake wiring
- Anything labeled `good first issue` or `help wanted`

## Licensing of Contributions

Resume-Libre is licensed under **AGPL-3.0**. By submitting a pull request you agree that your contribution is licensed under AGPL-3.0 too. Sign your commits off (`git commit -s`) to certify the [Developer Certificate of Origin](https://developercertificate.org/).

## Commit Conventions

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code restructuring (no behavior change) |
| `test:` | Adding or fixing tests |
| `chore:` | Tooling, dependencies, config |
| `ci:` | CI/CD changes |

Example: `feat: add LaTeX template selector to resume form`

## Pull Request Process

1. **Fork** the repo and create a branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Write tests** for your changes. Backend: `pytest`. Frontend: `npm test`.

3. **Run checks locally**:
   ```bash
   # Backend
   cd resume_generator_backend
   ruff check .
   pytest

   # Frontend
   cd resume-generator-frontend
   npm run lint
   npm test
   npm run build
   ```

4. **Open a PR** — fill out the PR template, link any related issues.

5. **CI must pass** — ruff, eslint, pytest, vitest, and build checks all green.

6. **Review** — a maintainer will review. Address feedback by pushing more commits.

## Pre-commit Hooks

The repo uses [pre-commit](https://pre-commit.com/). After cloning:

```bash
pip install pre-commit
pre-commit install
```

This runs ruff (Python), eslint (JS), prettier, and file hygiene checks on every commit.

## Database Migrations

Migrations are in `supabase/migrations/`. Apply them via the Supabase Dashboard SQL Editor or the Supabase CLI:

```bash
npx supabase db push
```

## Admin Access

To make a user an admin (for admin-only templates):

```sql
UPDATE profiles SET role = 'admin' WHERE email = 'your-email@example.com';
```

Run this in the Supabase Dashboard → SQL Editor.

## Reporting Issues

- **Bugs**: Use the bug report template on GitHub Issues
- **Features**: Use the feature request template
- **Security**: See [SECURITY.md](SECURITY.md) — do NOT open public issues for security vulnerabilities

## Questions?

Open a GitHub Discussion or join the conversation on Issues. We're friendly.
