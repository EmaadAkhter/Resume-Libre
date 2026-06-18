# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 1.x | ✅ |
| < 1.0 | ❌ |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, email **emdansari@gmail.com** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You will receive a response within **48 hours**. If the vulnerability is confirmed, a fix will be prioritized and a security advisory published.

## Security Measures in Place

| Area | Measure |
|---|---|
| Authentication | Supabase Auth (JWT-based, email/password) |
| Database | Row-Level Security (RLS) on all tables — users can only access their own data |
| API keys | Stored in `.env` (gitignored), never committed |
| Service role key | Backend-only, never exposed to frontend |
| CORS | Restricted to known origins |
| File uploads | Validated by extension and content type |

## What NOT to do

- Never commit `.env` files or API keys to the repository
- Never expose the Supabase `service_role` key in frontend code
- Never disable RLS policies in production
- Never log or print API keys, JWTs, or user credentials
