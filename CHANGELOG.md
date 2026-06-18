# Changelog

All notable changes to Resume-Libre will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
