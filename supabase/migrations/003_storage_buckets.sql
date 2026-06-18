-- ═══════════════════════════════════════════════════════
-- 003 — Storage Buckets
-- resume-uploads: user-uploaded existing resumes (PDF/DOCX/TXT)
-- template-uploads: user-uploaded template files (.md/.tex)
-- ═══════════════════════════════════════════════════════

INSERT INTO storage.buckets (id, name, public)
VALUES ('resume-uploads', 'resume-uploads', false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO storage.buckets (id, name, public)
VALUES ('template-uploads', 'template-uploads', false)
ON CONFLICT (id) DO NOTHING;

-- RLS on storage objects: users can only manage their own files
CREATE POLICY "resume_uploads_owner" ON storage.objects
  FOR ALL USING (
    bucket_id = 'resume-uploads'
    AND (auth.uid() = owner OR auth.uid() IS NOT NULL)
  );

CREATE POLICY "template_uploads_owner" ON storage.objects
  FOR ALL USING (
    bucket_id = 'template-uploads'
    AND (auth.uid() = owner OR auth.uid() IS NOT NULL)
  );
