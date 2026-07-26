# Privacy Policy

_Last updated: July 26, 2026_

Resume-Libre handles documents that contain personal information — names, contact details, employment history. This policy explains exactly what we do with that data. The short version: **we process your documents in memory and keep as little as possible.**

## What we collect

| Data | Stored? | Where | Why |
|---|---|---|---|
| Account email + password hash | Yes | Supabase (auth) | Sign-in |
| Resumes you save in the app | Yes | Supabase (Postgres, row-level security: only you can read yours) | The product — version history, branches |
| Files you upload to extract text (PDF/DOCX/TXT) | No — processed in memory, never written to disk | — | Text extraction for generation input |
| Files you upload to the app's storage bucket | Yes, until you delete them | Supabase Storage (owner-only access policy) | Your uploaded source resumes |
| GitHub username / README you point us at | Cached up to 1 hour | Redis | Avoid refetching |
| LinkedIn profile data (scraped or pasted) | Cached up to 24 hours | Redis | Avoid re-scraping |
| Generation metadata (timestamp, model, token counts, duration) | Yes | Server logs | Debugging, cost tracking |
| Published resume (explicit opt-in via the Publish button) | Yes, world-readable until you unpublish | Supabase public storage | Your shareable /r/ link |

## What we never do

- We never write your uploaded files to disk during processing.
- We never use your resume content to train models or for anything beyond serving your own request.
- We never sell or share your data with third parties.
- We never read your resumes — access is restricted by database row-level security to your own account.

## Third-party processors

- **Supabase** — authentication and database hosting.
- **OpenRouter** — resume text you submit for generation is sent to the LLM provider you configure. Their retention policies apply to the prompt content.
- **Apify** (optional) — LinkedIn profile scraping, only if configured and only for the URL you provide. You can always paste profile text instead.

## Deleting your data

Deleting a resume in the app deletes it permanently. Deleting your account removes your profile, resumes, and uploaded files. Redis caches expire automatically (1–24 hours).

## Self-hosting

Resume-Libre is open source (AGPL-3.0). If this policy doesn't fit your needs, you can run the entire stack on your own infrastructure — see the README.

## Contact

Questions: open an issue at https://github.com/EmaadAkhter/Resume-Libre or email the maintainer.
