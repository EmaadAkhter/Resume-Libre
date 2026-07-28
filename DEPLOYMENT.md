# Self-Hosting / Deployment Guide

Runs on any 2 GB Docker host; 4 GB is comfortable. Ubuntu 24.04 · Docker Compose · Caddy (auto-SSL). Swap `resumelibre.com` for your own domain throughout.

**Whole stack costs about $5/month.** Reference picks: a Hetzner CX22 (2 vCPU / 4 GB / 40 GB NVMe, ~€3.79) or any 2 GB VPS, plus a domain from Cloudflare Registrar (at-cost `.com`, ~$10/year, with free DNS and analytics). Supabase, Resend, Sentry, UptimeRobot and GHCR all sit inside their free tiers. Measured idle footprint is ~840 MB, peaking ~1.35 GB during a LaTeX compile.

## RAM budget (2 GB box)

| Service | RAM |
|---------|-----|
| OS + Docker daemon | ~260 MB |
| Caddy | ~30 MB |
| Frontend (nginx, static) | ~20 MB |
| Backend (FastAPI, 2 workers, capped 512 MB) | ~200–500 MB |
| LaTeX sidecar (capped 600 MB) | spikes during compile |
| Redis (capped 128 MB, allkeys-lru) | ~30 MB |

External (no VPS resources): Supabase (auth/DB/storage), OpenRouter (LLM), Apify (optional LinkedIn scraping).

## One-time VPS setup

```bash
ssh root@<vps-ip>
curl -fsSL https://get.docker.com | sh

# Swap absorbs LaTeX compile spikes
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable
```

**DNS** (before deploying — Caddy needs it to issue certs): `A @ → <vps-ip>`, `A www → <vps-ip>`.

## First deploy

```bash
# On the VPS
git clone https://github.com/EmaadAkhter/Resume-Libre.git /opt/resume-libre
cd /opt/resume-libre

# From your local machine: copy secrets
scp .env root@<vps-ip>:/opt/resume-libre/.env
```

Edit the repo `Caddyfile` if your domain differs, set `ALLOWED_ORIGINS=https://yourdomain.com` in `.env`, then:

```bash
# Option A — pull prebuilt images from GHCR (recommended on 1 vCPU):
docker compose -f docker-compose.prod.yml -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.prod.yml -f docker-compose.ghcr.yml up -d

# Option B — build on the box (slow on 1 vCPU, fine on 4+):
docker compose -f docker-compose.prod.yml up -d --build
```

Caddy provisions the Let's Encrypt cert on first request (~30 s).

> **GHCR + your own fork:** images are pushed by `.github/workflows/docker.yml` on `v*` tags. The frontend image bakes `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` at build time — set them as repo **Actions secrets** before tagging, and edit the image owner in `docker-compose.ghcr.yml`.

## Supabase setup

1. Create a free project, grab URL + anon + service keys into `.env`.
2. SQL Editor → run each file in `supabase/migrations/` in order (001 → 006), then `supabase/seed.sql`.
3. Auth → URL Configuration: set Site URL to `https://yourdomain.com` (makes email verification/reset links work).
4. **Custom SMTP — do this before taking real signups.** Supabase's built-in
   email sender is capped at **2 messages per hour for the whole project**, so
   the third person who registers never gets a confirmation mail. Create a free
   [Resend](https://resend.com) account (3,000 emails/month), then Auth → SMTP
   Settings → enter its host/port/user/password and a verified From address.
   Afterwards raise Auth → Rate Limits (custom SMTP starts at 30/hour). Custom
   SMTP is also the only way to edit the auth email templates.
5. Optional admin: `UPDATE profiles SET role='admin' WHERE email='you@example.com';`

## Environment variables

Everything lives in one repo-root `.env` — see [.env.example](.env.example) for the annotated list. Production-specific:

| Variable | Value |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://yourdomain.com` |
| `VITE_API_URL` | `/api` (nginx proxies to backend) |
| `ALLOW_DEMO_REQUESTS` | `true` to let anonymous visitors run the zero-cost canned demo |

## Updating

```bash
cd /opt/resume-libre && git pull
docker compose -f docker-compose.prod.yml -f docker-compose.ghcr.yml pull
docker compose -f docker-compose.prod.yml -f docker-compose.ghcr.yml up -d
```

## Smoke test

- [ ] `https://yourdomain.com` shows the landing page (green lock)
- [ ] `https://yourdomain.com/api/health` → `{"status": "healthy", ...}`
- [ ] Register → verification email arrives (via custom SMTP) → login works
- [ ] Publish a resume → `/r/<user_id>` loads for a logged-out visitor
- [ ] Generation streams and the PDF preview renders
- [ ] `/demo` works logged-out (if `ALLOW_DEMO_REQUESTS=true`)
- [ ] Generate 11× in an hour → 11th returns 429; still 429 after `docker compose restart backend`
- [ ] `docker stats` — backend under 512 MB, box has headroom

## Cost guardrails

- Set a **hard spend cap in the OpenRouter dashboard** — the single biggest launch-day risk is uncapped LLM spend.
- **Free OpenRouter models are capped at 50 requests/day** until you have bought $10 of credits, which raises the daily limit to 1,000 permanently (it stays there even after the balance runs out). A launch spike exhausts 50 in minutes, so buy the $10 before you announce anything.
- Rate limits are Redis-backed and per-user/IP (`core/limiter.py`).
- Keep `APIFY_API_TOKEN` empty unless you need URL scraping; paste-text input costs nothing and avoids the scraping ToS question entirely.

## Troubleshooting

- **SSL not issuing** — DNS not propagated (`dig yourdomain.com`) or 80/443 blocked (`ufw status`).
- **Backend OOM** — LaTeX spikes; the swapfile absorbs them. `docker compose -f docker-compose.prod.yml restart backend`.
- **Slow compiles** — the `tectonic-cache` volume persists downloaded packages; first compile is always slowest.
- **Blank page after refresh** — nginx SPA fallback is in `resume-generator-frontend/nginx.conf`.
- **Logs** — `docker compose -f docker-compose.prod.yml logs -f backend|frontend|caddy|latex-service`.
