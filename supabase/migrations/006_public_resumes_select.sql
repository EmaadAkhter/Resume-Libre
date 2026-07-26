-- ═══════════════════════════════════════════════════════
-- 006 — Missing SELECT policy on public-resumes objects
--
-- storage.upload(..., { upsert: true }) makes the storage API check
-- whether the object exists (a SELECT under the caller's RLS) before
-- inserting/updating. 005 granted INSERT/UPDATE/DELETE but no SELECT,
-- so every publish failed with "new row violates row-level security
-- policy". The bucket is public anyway — objects are world-readable
-- by URL — so a world SELECT policy changes nothing about exposure.
-- ═══════════════════════════════════════════════════════

CREATE POLICY "public_resumes_storage_select" ON storage.objects
  FOR SELECT USING (bucket_id = 'public-resumes');
