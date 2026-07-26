-- ═══════════════════════════════════════════════════════
-- 004 — Fix storage RLS: owner-only access
--
-- 003 had `auth.uid() = owner OR auth.uid() IS NOT NULL`,
-- which let ANY logged-in user read/write EVERY user's
-- uploaded files (resumes are PII). Recreate both policies
-- scoped strictly to the file owner.
--
-- Manual verification after applying:
--   1. Upload a file as user A.
--   2. As user B, storage.from('resume-uploads').download(<A's path>)
--      → must fail with a 4xx, not return the file.
-- ═══════════════════════════════════════════════════════

DROP POLICY IF EXISTS "resume_uploads_owner" ON storage.objects;
DROP POLICY IF EXISTS "template_uploads_owner" ON storage.objects;

CREATE POLICY "resume_uploads_owner" ON storage.objects
  FOR ALL USING (
    bucket_id = 'resume-uploads'
    AND auth.uid() = owner
  )
  WITH CHECK (
    bucket_id = 'resume-uploads'
    AND auth.uid() = owner
  );

CREATE POLICY "template_uploads_owner" ON storage.objects
  FOR ALL USING (
    bucket_id = 'template-uploads'
    AND auth.uid() = owner
  )
  WITH CHECK (
    bucket_id = 'template-uploads'
    AND auth.uid() = owner
  );
