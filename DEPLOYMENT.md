# Deployment Guide — Resume-Libre

Hostinger KVM2 · Ubuntu 24.04 · Docker Compose · Caddy (SSL)

---

## Infrastructure

| Service | RAM | Notes |
|---------|-----|-------|
| OS (Ubuntu) | ~200 MB | Base |
| Docker daemon | ~60 MB | |
| Caddy | ~30 MB | Reverse proxy + auto SSL |
| Frontend (nginx, static) | ~20 MB | Serves Vite build |
| Backend (FastAPI, 4 workers) | ~300–500 MB | Spikes during LaTeX compile |
| **Total** | **~700 MB–1 GB** | Fits in 2 GB KVM2 |

**External services (no VPS change needed):**
- Supabase — auth, DB, storage
- OpenRouter — LLM
- Resend — transactional email (optional)
- Apify — LinkedIn scraping (optional)

---

## Prerequisites

### Local machine
- SSH key added to Hostinger VPS
- `.env` file with all secrets (see [Environment Variables](#environment-variables))
- Domain `resumelibre.com` purchased and DNS managed

### VPS (one-time setup)
```bash
# SSH in
ssh root@<vps-ip>

# Install Docker
curl -fsSL https://get.docker.com | sh

# Add swap (safety net for LaTeX spikes)
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### DNS
Point both records to the VPS IP before deploying (Caddy needs DNS to issue certs):

| Type | Name | Value |
|------|------|-------|
| A | `@` | `<vps-ip>` |
| A | `www` | `<vps-ip>` |

---

## Files to Create Before First Deploy

These files live in the repo but are not committed (secrets / provider-specific).

### `Caddyfile` (repo root)
```
resumelibre.com, www.resumelibre.com {
    reverse_proxy frontend:80
}
```

### `.env` (repo root)
Copy from `.env.example` and fill in all values. See [Environment Variables](#environment-variables).

---

## First Deploy

```bash
# On VPS
git clone <repo-url> /opt/resume-libre
cd /opt/resume-libre

# Copy secrets from local machine (run this locally)
scp .env root@<vps-ip>:/opt/resume-libre/.env
scp Caddyfile root@<vps-ip>:/opt/resume-libre/Caddyfile

# Back on VPS — build and start
docker compose -f docker-compose.prod.yml up -d --build

# Tail logs to confirm startup
docker compose -f docker-compose.prod.yml logs -f
```

Caddy auto-provisions the Let's Encrypt cert on first request. Allow ~30 seconds.

---

## Updating the App

```bash
# On VPS
cd /opt/resume-libre
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Zero-downtime: Compose replaces containers one at a time. Backend health check ensures frontend waits for it.

---

## Environment Variables

### Backend (`.env`, server-only)

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key (`sk-or-v1-...`) |
| `OPENROUTER_MODEL` | Model string, e.g. `anthropic/claude-3-5-sonnet` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (admin) |
| `APIFY_API_TOKEN` | Apify token for LinkedIn scraping |
| `LINKEDIN_COOKIE` | `li_at` cookie value for LinkedIn |
| `TECTONIC_PATH` | Path to tectonic binary (default: `/usr/local/bin/tectonic`) |

### Frontend (`.env`, baked into build via Docker build args)

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Same as `SUPABASE_URL` above |
| `VITE_SUPABASE_ANON_KEY` | Same as `SUPABASE_ANON_KEY` above |
| `VITE_API_URL` | Set to `/api` in production (nginx proxies to backend) |

---

## docker-compose.prod.yml Changes Needed

The current `docker-compose.prod.yml` needs these changes before first deploy:

1. **Add Caddy service** with ports 80/443
2. **Remove exposed ports** from `backend` and `frontend` (internal only)
3. **Add build args** for frontend Supabase vars
4. **Add Caddy volumes** for cert persistence

See the [implementation plan](../.claude/plans/here-s-the-full-stack-fluffy-cupcake.md) for exact diffs.

---

## Smoke Test Checklist

After deploy, verify:

- [ ] `https://resumelibre.com` loads the app (green SSL lock)
- [ ] `https://resumelibre.com/api/health` returns `{"status": "ok"}`
- [ ] Login / register works (Supabase)
- [ ] Resume generation works (OpenRouter)
- [ ] PDF export works (LaTeX / Tectonic)
- [ ] `docker stats` — backend memory under ~500 MB

---

## Troubleshooting

### SSL cert not issuing
- DNS A records not propagated yet — wait up to 24h, check with `dig resumelibre.com`
- Ports 80/443 not open — verify `ufw status`

### Backend OOM / killed
- LaTeX compile spikes RAM — swap file absorbs it (see VPS setup above)
- `docker compose -f docker-compose.prod.yml restart backend`

### Tectonic cache miss on every request
- Mount a named volume for the Tectonic cache directory if compile times are slow
- Cache path: `/root/.cache/Tectonic` inside the container

### Frontend shows blank page / 404 on refresh
- Nginx SPA fallback already configured in `nginx.conf` — if broken, check `location /` block

### Check logs
```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs frontend
docker compose -f docker-compose.prod.yml logs caddy
```

---

## Optional: WhatsApp OTP (OpenWA / Baileys)

Not included in base deploy. Add when needed:
- ~100–200 MB extra RAM
- Add `openwa` service to `docker-compose.prod.yml`
- Requires QR code scan on first run (`docker attach` to the container)
