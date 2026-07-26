# Changelog

All notable changes to Resume-Libre will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (launch prep — July 2026)
- **ATS parseability checker**: 31 deterministic checks in six categories (extraction, layout, typography, contact, content & writing, file) with reasons, fixes, and measured threshold meters — no aggregate score by design. Free at `/ats-check`, no account needed; ~24 checks for DOCX
- **ATS view in the editor** (Edit | Preview | ATS): every compiled PDF is auto-checked; **"Fix issues & regenerate"** feeds findings back into the prompt under keep-facts rules
- **Field extraction** ("what an ATS would extract"): rules-first with per-field confidence; signed-in AI resolution for ambiguous fields (double-sampled, schema-validated)
- **ATS keyword match**: post-generation gap analysis vs a job description or one of 10 role presets
- **Public resume hosting**: one-click publish to `/r/<user_id>`, unpublish any time
- **Fresher Wizard**: guided 7-profession intake for users without GitHub/LinkedIn
- **LinkedIn paste-text input** (default) — Apify scraping now optional
- **Zero-config demo mode** (`DEMO_MODE=true`): full stack with no API keys
- Landing page, sidebar app shell, emerald design system, Inter font
- 5 built-in LaTeX templates (Awesome, ModernCV, AltaCV, Deedy, Friggeri styles) + TEMPLATES.md contribution guide
- Production deploy: Caddyfile, GHCR image overlay, 2GB-VPS sizing, public DEPLOYMENT.md
- Calibration harness (`scripts/calibrate_ats.py`) per the PRD procedure

### Fixed
- Storage RLS let any logged-in user read every user's uploads (migration 004)
- Generation/export endpoints required no auth; rate limits were per-worker in-memory (now Redis-backed, per-user)
- Export menu offered Markdown/DOCX formats that produced garbage from the LaTeX pipeline
- Custom system prompt from the modal never reached generation
- Glued-word PDF extractions misdiagnosed as layout problems; resume length counted glued blobs

### Changed
- **License changed from MIT to AGPL-3.0.** All code from this point forward is licensed under AGPL-3.0. Code published up to and including commit `dee7144` remains available under the MIT license.

### Added
- Vite build tool (replacing Create React App)
- Supabase authentication (email/password with JWT)
- PostgreSQL database schema with Row-Level Security
- Resume versioning system (Git-like: branches, tags, commits, diffs)
- Template management (DB-stored, user-uploaded `.md`/`.tex`, admin-only templates)
- LaTeX resume generation with Tectonic compilation
- Server-Sent Events (SSE) for streaming AI generation
- Event-driven architecture (mitt event bus on frontend, EventBus on backend)
- ResumePipeline with pluggable middleware hooks
- Docker support (dev + prod) with docker-compose
- Pre-commit hooks (ruff, eslint, prettier)
- GitHub Actions CI/CD (lint, test, build, Docker push to GHCR)
- Backend test suite (pytest)
- Frontend test suite (vitest + testing-library)
- GitHub issue/PR templates
- CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md

### Changed
- Migrated frontend from Create React App to Vite
- Replaced MCP server with direct GitHub API call via httpx
- Simplified OpenRouter integration to single key/model (removed 6-key rotation)
- System prompt rewritten to support both Markdown and LaTeX output

### Removed
- MCP_SERVER/ directory (replaced by direct GitHub API call)
- Multi-key/multi-model rotation logic
- Create React App dependencies (react-scripts)

## [0.1.0] - 2025-01-15

### Added
- AI-powered resume generation via OpenRouter
- GitHub README fetching via MCP
- Resume upload (PDF/DOCX/TXT extraction)
- Live Markdown editor with preview
- Export to PDF/DOCX/Markdown
- Custom system prompt editing
- Responsive mobile/desktop UI
- 6-key OpenRouter rotation for rate limit distribution
