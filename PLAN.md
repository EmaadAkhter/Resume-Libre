# Fresher Wizard + JD Matcher + LinkedIn Integration — Implementation Plan

## Overview

Three features, 10 files changed (2 new, 8 modified), ~435 net lines.

| Feature | Scope |
|---------|-------|
| **Fresher Wizard** | 6-step guided intake with field-swapped labels per profession |
| **JD Matcher** | Paste job description → AI tailors resume to match |
| **LinkedIn Scraper** | Bright Data integration → pull work history, education, skills |

---

## Data Flow

```
User Interface
├─ Simple Mode
│   ├─ GitHub username → fetch_github_readme()
│   ├─ LinkedIn URL   → fetch_linkedin_profile() → Bright Data
│   └─ JD textarea    → job_description
│
├─ Wizard Mode
│   ├─ Step 0: Profession picker (7 fields)
│   ├─ Steps 1-6: Collect structured data → builds text → additional_info
│   ├─ LinkedIn URL → linkedin_url (passed to pipeline)
│   └─ JD textarea  → job_description (collapsible at end)
│
└─ Pipeline (sequential)
    1. fetch_github_readme(github_username)
    2. fetch_linkedin_profile(linkedin_url)        ← NEW
    3. build_user_prompt(readme, linkedin, info, jd)
    4. AI generates → profession-formatted, JD-tailored resume
```

---

## File 1: `FresherWizard.jsx` — NEW (~280 lines)

**Location:** `resume-generator-frontend/src/components/FresherWizard.jsx`

### Profession Config Object

One object, 7 profession entries. Each defines swapped labels for 4 steps:

| Step | Software | Finance | Medical | Legal | Design | MBA | General |
|------|----------|---------|---------|-------|--------|-----|---------|
| 3. Skills | Technical Skills | Financial Skills | Clinical Skills | Legal Skills | Design Skills | Mgmt Skills | Skills |
| 4. Projects | Projects | Deal Experience | Clinical Rotations | Clerkships | Design Projects | Case Competitions | Key Projects |
| 5. Experience | Internships | Work Experience | Internships/Residency | Work Experience | Work Experience | Work Experience | Work Experience |
| 6. Achievements | Achievements | Certifications | Licenses & Research | Bar & Pubs | Awards & Exhibitions | Achievements | Achievements |

Each entry specifies: `title`, `placeholder`, `hint`, `nameLabel`, `techLabel`, `descLabel`, `linkLabel`, `linkPlaceholder`.

### Wizard Steps

| Step | Content |
|------|---------|
| 0 — Profession | Radio card grid of 7 professions |
| 1 — Basic Info | Name, Email, Phone, Location, LinkedIn URL |
| 2 — Education | College, Degree, Field, Year, CGPA |
| 3 — Skills | Single textarea (label swaps per profession) |
| 4 — Projects | Repeatable: Title, Tech Stack, Description, GitHub/Portfolio URL (label swaps) |
| 5 — Experience | Repeatable: Company, Role, Duration, Description (label swaps) |
| 6 — Achievements | Single textarea (label swaps per profession) |

### Step Navigation

- Step indicator at top: `[1] [2] [3] [4] [5] [6]`
- Back / Next buttons
- Step 6 shows "Generate Resume" button + collapsible JD textarea

### Structured Text Builder

On "Generate Resume", the wizard builds a structured text block that fills `additional_info`:

```
--- PROFESSION ---
Software / IT

--- BASIC INFO ---
Name: John Doe
Email: john@example.com

--- EDUCATION ---
B.Tech CSE | ABC College | 2025 | CGPA: 8.5/10

--- TECHNICAL SKILLS ---
Python, JavaScript, React, Docker

--- PROJECTS ---
1. E-Commerce Platform | React, Node.js
   GitHub: https://github.com/user/ecommerce
   Full-stack app with payment gateway...

--- INTERNSHIPS ---
1. SWE Intern at XYZ Corp (Jun 2024 - Aug 2024)
   Built REST APIs, reduced latency 30%

--- ACHIEVEMENTS ---
AWS Certified Cloud Practitioner
Winner, Hackathon XYZ 2024
```

Section headers use profession-specific titles from the config.

### Props

```jsx
<FresherWizard
  onGenerate={onGenerate}
  loading={loading}
  backendConnected={backendConnected}
  templates={templates}
  selectedTemplate={selectedTemplate}
  onSelectTemplate={onSelectTemplate}
/>
```

---

## File 2: `services/linkedin.py` — NEW (~45 lines)

**Location:** `resume_generator_backend/services/linkedin.py`

Pattern: identical structure to `github.py`.

```python
import os, httpx

async def fetch_linkedin_profile(profile_url: str) -> dict:
    api_key = os.getenv("BRIGHTDATA_API_KEY")
    if not api_key:
        return {}

    # POST profile URL to Bright Data trigger API
    # Poll for snapshot results (async scraping)
    # Returns dict with: profile, experience[], education[], skills[], certifications[]
    # On failure: returns {}
```

**Key behaviors:**
- Silent skip if `BRIGHTDATA_API_KEY` not set (returns `{}`)
- Polls up to 10 times (~30s timeout)
- Returns first matching profile result

---

## File 3: `ResumeForm.jsx` — MODIFIED (+40 lines)

**Location:** `resume-generator-frontend/src/components/ResumeForm.jsx`

### Change 1: Mode Toggle (top of form, before GitHub field)

```jsx
const [mode, setMode] = useState('simple')
```

Two-button toggle: `Quick Form | Step-by-Step Wizard`

### Change 2: Conditional Render

`mode === 'wizard'` → renders `<FresherWizard />`  
`mode === 'simple'` → renders existing form + new LinkedIn URL field + JD textarea

### Change 3: LinkedIn URL Field (simple mode, after GitHub)

```jsx
<label>LinkedIn Profile URL</label>
<input type="url" placeholder="https://linkedin.com/in/username" />
<p>Bright Data status notice</p>
```

State: `const [linkedinUrl, setLinkedinUrl] = useState('')`

### Change 4: JD Textarea (simple mode, collapsible after Additional Info)

```jsx
<details>
  <summary>🎯 Target a specific job (optional)</summary>
  <textarea placeholder="Paste job description..." />
</details>
```

State: `const [jobDescription, setJobDescription] = useState('')`

### Change 5: Generate Params

```js
onGenerate({
  ...existingParams,
  linkedin_url: linkedinUrl || null,
  job_description: jobDescription || null,
})
```

---

## File 4: `useGenerationStream.js` — MODIFIED (+2 lines)

**Location:** `resume-generator-frontend/src/hooks/useGenerationStream.js`

```js
// After line 10 (github_username)
if (params.linkedin_url) queryParams.set('linkedin_url', params.linkedin_url)
// After line 14 (custom_system_prompt)
if (params.job_description) queryParams.set('job_description', params.job_description)
```

---

## File 5: `schemas/resume.py` — MODIFIED (+2 lines)

**Location:** `resume_generator_backend/schemas/resume.py`

```python
# After line 6 (github_username)
linkedin_url: Optional[str] = None
# After line 7 (additional_info)
job_description: Optional[str] = None
```

---

## File 6: `routers/generation.py` — MODIFIED (+4 lines)

**Location:** `resume_generator_backend/routers/generation.py`

**POST `/generate-resume`:** Accept `linkedin_url`, `job_description` from request body. Pass to `pipeline.run()`.

**GET `/generate-resume-stream`:** Accept `linkedin_url`, `job_description` as Query params. Pass to `pipeline.run_stream()`.

---

## File 7: `services/pipeline.py` — MODIFIED (+10 lines)

**Location:** `resume_generator_backend/services/pipeline.py`

### `run()` and `run_stream()` — Add parameters:

```python
linkedin_url: str = "",
job_description: str = "",
```

### LinkedIn Fetch Stage (after GitHub, before prompt building):

```python
linkedin_data = await fetch_linkedin_profile(linkedin_url) if linkedin_url else {}
```

### Prompt builder call — pass both:

```python
user_prompt = build_user_prompt(
    github_username, readme_content, linkedin_data,
    additional_info, priority, resume_template, job_description,
)
```

---

## File 8: `services/prompt.py` — MODIFIED (+45 lines)

**Location:** `resume_generator_backend/services/prompt.py`

### Function signature:

```python
def build_user_prompt(
    github_username: str,
    readme_content: str,
    linkedin_data: dict,        # NEW
    additional_info: str,
    priority: str,
    resume_template: str = None,
    job_description: str = "",  # NEW
) -> str:
```

### Add LinkedIn section (after GitHub section, before Additional Info):

```python
if linkedin_data and linkedin_data.get("profile"):
    prompt += "\n\n--- LinkedIn Profile Data ---\n"
    # profile fields: name, headline, location
    # experience[], education[], skills[], certifications[]
```

### Add JD targeting block (after "--- End of Information ---"):

```python
if job_description and job_description.strip():
    prompt += f"""
--- TARGET JOB DESCRIPTION ---
{job_description}

TARGETING INSTRUCTIONS:
- Naturally incorporate relevant keywords from the job description
- Reorder experience/projects so the most relevant appear first
- Prioritize skills and technologies mentioned in the JD
- Do NOT fabricate — rephrase and emphasize existing data only
- Match the role's seniority level and industry tone
"""
```

---

## File 9: `system_promt.txt` — MODIFIED (+6 lines)

**Location:** `resume_generator_backend/system_promt.txt`

Add before output format section (after line 83):

```
JOB DESCRIPTION TARGETING (if provided):
- Keywords from the JD should appear naturally in the resume
- Reorder bullet points to match JD priorities
- Never invent experience — only reweight existing content
- Match the tone: corporate for banks, technical for startups, formal for legal/medical
```

---

## File 10: `.env` — MODIFIED (+1 line)

```
BRIGHTDATA_API_KEY=
```

---

## Deliberate Simplifications

| Decision | Why |
|----------|-----|
| One wizard, 7 config entries | Not 7 components. Labels swap, structure stays. |
| Profession tuning = prompt-only | No separate templates. Section headers in text + system prompt handle it. |
| LinkedIn silent skip if no API key | No feature flags or conditional UI. Returns `{}`, prompt skips empty section. |
| JD matching = prompt instructions | No NLP library, no keyword extraction. AI does it from raw text. |
| Bright Data polling, not webhook | One less moving part. Poll until timeout or success. |
| Wizard data in `additional_info` string | No DB tables, no backend schema for wizard. Zero backend debt. |
| Project links in text, not fetched | AI hyperlinks from URL in text. Per-repo fetch is future scope. |

---

## What's NOT Built

- No database storage for profile data
- No caching for Bright Data results
- No per-project GitHub README fetching
- No ORCID / Behance / Kaggle / HuggingFace / OpenAlex
- No profession-specific resume templates (swapped labels + AI is sufficient)
- No webhook callback for Bright Data
- No Naukri-specific output format
