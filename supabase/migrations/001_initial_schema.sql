-- ═══════════════════════════════════════════════════════
-- 001 — Initial Schema
-- Tables: profiles, templates, resumes, resume_versions, branches, tags
-- ═══════════════════════════════════════════════════════

-- ─── Extensions ─────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Profiles (extends auth.users) ─────────────────
CREATE TABLE profiles (
  id           UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email        TEXT NOT NULL,
  display_name TEXT DEFAULT '',
  role         TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-create profile when a user signs up
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO profiles (id, email)
  VALUES (NEW.id, NEW.email);
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ─── Templates ──────────────────────────────────────
CREATE TABLE templates (
  id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name          TEXT NOT NULL,
  description   TEXT DEFAULT '',
  content       TEXT NOT NULL,
  format        TEXT NOT NULL CHECK (format IN ('md', 'tex')),
  is_admin_only BOOLEAN NOT NULL DEFAULT FALSE,
  is_public     BOOLEAN NOT NULL DEFAULT TRUE,
  created_by    UUID REFERENCES auth.users(id) ON DELETE SET NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Resumes ────────────────────────────────────────
CREATE TABLE resumes (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id        UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name           TEXT NOT NULL,
  template_id    UUID REFERENCES templates(id) ON DELETE SET NULL,
  current_branch TEXT NOT NULL DEFAULT 'main',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Resume Versions (commits) ──────────────────────
CREATE TABLE resume_versions (
  id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  resume_id         UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  parent_version_id UUID REFERENCES resume_versions(id) ON DELETE SET NULL,
  branch_name       TEXT NOT NULL DEFAULT 'main',
  message           TEXT DEFAULT '',
  content           TEXT NOT NULL,
  latex_content     TEXT,
  generation_prompt TEXT,
  template_id       UUID REFERENCES templates(id) ON DELETE SET NULL,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_resume_versions_resume_id ON resume_versions(resume_id);
CREATE INDEX idx_resume_versions_branch ON resume_versions(resume_id, branch_name);

-- ─── Branches ───────────────────────────────────────
CREATE TABLE branches (
  id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  resume_id       UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  head_version_id UUID REFERENCES resume_versions(id) ON DELETE SET NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(resume_id, name)
);

-- ─── Tags ───────────────────────────────────────────
CREATE TABLE tags (
  id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  resume_id   UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  version_id  UUID NOT NULL REFERENCES resume_versions(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(resume_id, name)
);

-- ─── Updated_at trigger for resumes ─────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER resumes_updated_at
  BEFORE UPDATE ON resumes
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
