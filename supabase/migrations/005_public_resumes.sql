-- ═══════════════════════════════════════════════════════
-- 005 — Public resume hosting
--
-- One published resume per user, world-readable at /r/<user_id>.
-- The compiled PDF lives in the public `public-resumes` storage
-- bucket as <user_id>.pdf; this table carries the metadata.
-- ═══════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS public_resumes (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
  display_name TEXT NOT NULL DEFAULT 'Resume',
  published_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public_resumes ENABLE ROW LEVEL SECURITY;

-- Anyone (including anonymous visitors) can read published metadata.
CREATE POLICY "public_resumes_read" ON public_resumes
  FOR SELECT USING (true);

-- Only the owner can publish, update, or take down their entry.
CREATE POLICY "public_resumes_insert" ON public_resumes
  FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "public_resumes_update" ON public_resumes
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
CREATE POLICY "public_resumes_delete" ON public_resumes
  FOR DELETE USING (auth.uid() = user_id);

-- Public bucket for the compiled PDFs (public = readable by URL).
INSERT INTO storage.buckets (id, name, public)
VALUES ('public-resumes', 'public-resumes', true)
ON CONFLICT (id) DO NOTHING;

-- Owners write only their own <user_id>.pdf; the bucket being public
-- covers reads.
CREATE POLICY "public_resumes_storage_write" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'public-resumes'
    AND name = auth.uid()::text || '.pdf'
  );
CREATE POLICY "public_resumes_storage_update" ON storage.objects
  FOR UPDATE USING (
    bucket_id = 'public-resumes'
    AND name = auth.uid()::text || '.pdf'
  );
CREATE POLICY "public_resumes_storage_delete" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'public-resumes'
    AND name = auth.uid()::text || '.pdf'
  );
