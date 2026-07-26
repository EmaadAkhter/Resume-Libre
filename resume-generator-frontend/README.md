# Resume-Libre Frontend

React 19 + Vite + Tailwind CSS. See the [root README](../README.md) for the full picture.

## Develop

```bash
npm install
npm run dev        # Vite dev server on http://localhost:5173
```

Requires `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, and `VITE_API_URL` (see `../.env.example`). Vite reads them from the repo-root `.env`.

## Test & lint

```bash
npx vitest run     # unit tests (jsdom)
npx eslint src     # lint
```

## Build

```bash
npm run build      # production bundle in dist/
```

The production Dockerfile is multi-stage: Vite build → nginx serving `dist/` with `/api/*` proxied to the backend (SSE buffering disabled). Supabase env vars are baked in at build time via build args.

## Layout

- `src/pages/` — route-level pages (Landing, Login, Register, Dashboard, ResumeEditor)
- `src/components/` — UI components (ResumeForm, ExportMenu, version history, …)
- `src/hooks/` — `useGenerationStream` (SSE), `useSupabaseAuth`, `useTemplates`
- `src/lib/` — Supabase client, API fetch helper (`api.js`), mitt event bus
