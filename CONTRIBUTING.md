# Contributing to Resume-Libre

Thanks for your interest in contributing! This guide will get you set up and shipping code fast.

## Prerequisites

- **Node.js 20+** — [download](https://nodejs.org/)
- **Python 3.11+** — [download](https://www.python.org/downloads/)
- **Docker** + **Docker Compose** — [download](https://docs.docker.com/get-docker/)
- **Tectonic** (LaTeX engine) — `curl -fsSL https://drop-sh.fullyjustified.net | sh` (macOS/Linux) or see [releases](https://github.com/tectonic-typesetting/tectonic/releases)
- An [OpenRouter](https://openrouter.ai/keys) API key (free tier works)
- A [Supabase](https://supabase.com) project (free tier works)

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/EmaadAkhter/Resume-Libre.git
cd Resume-Libre

# 2. Copy environment
cp .env.example .env
# Edit .env with your real keys

# 3. Run everything
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
