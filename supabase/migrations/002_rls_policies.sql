-- ═══════════════════════════════════════════════════════
-- 002 — Row Level Security Policies
-- Users can only access their own data.
-- Templates: public ones visible to all, admin-only to admins,
--   private to creator.
-- Also seeds the admin user.
-- ═══════════════════════════════════════════════════════

-- ─── Helper: check if current user is admin ─────────
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
STABLE
AS $$
  SELECT EXISTS (
    SELECT 1 FROM profiles
    WHERE id = auth.uid() AND role = 'admin'
  );
$$;

-- ─── Profiles ───────────────────────────────────────
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "profiles_select_self" ON profiles;
CREATE POLICY "profiles_select_self" ON profiles
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "profiles_select_admin" ON profiles;
CREATE POLICY "profiles_select_admin" ON profiles
  FOR SELECT USING (is_admin());

DROP POLICY IF EXISTS "profiles_update_self" ON profiles;
CREATE POLICY "profiles_update_self" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- ─── Templates ──────────────────────────────────────
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "templates_read" ON templates;
CREATE POLICY "templates_read" ON templates
  FOR SELECT USING (
    (is_public = true AND is_admin_only = false)
    OR is_admin()
    OR created_by = auth.uid()
  );

DROP POLICY IF EXISTS "templates_insert" ON templates;
CREATE POLICY "templates_insert" ON templates
  FOR INSERT WITH CHECK (
    auth.uid() IS NOT NULL
    AND (
      created_by = auth.uid()
      OR is_admin()
    )
  );

DROP POLICY IF EXISTS "templates_update" ON templates;
CREATE POLICY "templates_update" ON templates
  FOR UPDATE USING (
    created_by = auth.uid() OR is_admin()
  );

DROP POLICY IF EXISTS "templates_delete" ON templates;
CREATE POLICY "templates_delete" ON templates
  FOR DELETE USING (
    created_by = auth.uid() OR is_admin()
  );

-- ─── Resumes ────────────────────────────────────────
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "resumes_owner_all" ON resumes;
CREATE POLICY "resumes_owner_all" ON resumes
  FOR ALL USING (auth.uid() = user_id);

-- ─── Resume Versions ────────────────────────────────
ALTER TABLE resume_versions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "versions_owner_all" ON resume_versions;
CREATE POLICY "versions_owner_all" ON resume_versions
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE id = resume_versions.resume_id
      AND user_id = auth.uid()
    )
  );

-- ─── Branches ───────────────────────────────────────
ALTER TABLE branches ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "branches_owner_all" ON branches;
CREATE POLICY "branches_owner_all" ON branches
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE id = branches.resume_id
      AND user_id = auth.uid()
    )
  );

-- ─── Tags ───────────────────────────────────────────
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "tags_owner_all" ON tags;
CREATE POLICY "tags_owner_all" ON tags
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM resumes
      WHERE id = tags.resume_id
      AND user_id = auth.uid()
    )
  );

-- ─── Seed Admin User ────────────────────────────────
-- This runs after the profile is auto-created on signup.
-- If the user hasn't signed up yet, this is a no-op.
-- Run this again after the admin signs up for the first time.
UPDATE profiles
SET role = 'admin'
WHERE email = 'emdansari@gmail.com';
