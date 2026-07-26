import re
from pathlib import Path


def load_template() -> str:
    current_dir = Path(__file__).parent
    template_path = current_dir.parent / "template.md"

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"template.md not found at {template_path}")


TEMPLATE_STRUCTURE = load_template()


def extract_contact_info(text: str) -> dict:
    info = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": "",
    }

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
    )
    if email_match:
        info["email"] = email_match.group(0)

    phone_match = re.search(
        r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
    )
    if phone_match:
        info["phone"] = phone_match.group(0)

    linkedin_match = re.search(r"linkedin\.com/in/([A-Za-z0-9-]+)", text)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(1)

    return info


def build_user_prompt(
    github_username: str,
    readme_content: str,
    additional_info: str,
    priority: str,
    resume_template: str | None = None,
    linkedin_data: dict | None = None,
    job_description: str = "",
    ats_feedback: str | None = None,
    hf_data: dict | None = None,
    orcid_data: dict | None = None,
    github_readmes: list | None = None,
    linkedin_profiles: list | None = None,
    hf_profiles: list | None = None,
    orcid_profiles: list | None = None,
) -> str:
    """Build the generation prompt from any number of profile sources.

    The list params hold repeatable entries: github_readmes as
    (username, readme) pairs, hf_profiles as (username, data) pairs,
    linkedin_profiles / orcid_profiles as data dicts. The singular
    readme_content / linkedin_data / hf_data / orcid_data params are
    deprecated aliases folded into the lists when those are empty.
    """
    github_readmes = list(github_readmes or [])
    linkedin_profiles = list(linkedin_profiles or [])
    hf_profiles = list(hf_profiles or [])
    orcid_profiles = list(orcid_profiles or [])

    if not github_readmes and readme_content and readme_content.strip():
        github_readmes.append((github_username, readme_content))
    if not linkedin_profiles and linkedin_data:
        linkedin_profiles.append(linkedin_data)
    if not hf_profiles and hf_data:
        hf_profiles.append(("", hf_data))
    if not orcid_profiles and orcid_data:
        orcid_profiles.append(orcid_data)

    first_readme = github_readmes[0][1] if github_readmes else ""
    contact = extract_contact_info(additional_info + " " + first_readme)

    if github_username:
        contact["github"] = github_username

    priority_label = {
        "experience": "Experience First — lead with work history",
        "projects": "Projects First — lead with projects",
        "balanced": "Balanced — equal weight between experience and projects",
    }.get(priority, priority.title())

    prompt = f"""Format this information into a one-page, ATS-friendly resume.

PRIORITY: {priority_label}

AVAILABLE INFORMATION:
"""

    if github_username:
        prompt += f"\nGitHub Username: {github_username}"

    if contact["email"]:
        prompt += f"\nEmail: {contact['email']}"

    if contact["phone"]:
        prompt += f"\nPhone: {contact['phone']}"

    if contact["linkedin"]:
        prompt += f"\nLinkedIn: {contact['linkedin']}"

    if github_readmes:
        for gh_username, gh_readme in github_readmes:
            prompt += f"\n\n--- GitHub Profile README: {gh_username} ---\n"
            prompt += gh_readme
    else:
        prompt += "\n\n--- GitHub Profile Content ---\n"
        prompt += "(No GitHub profile content available)"

    for li_data in linkedin_profiles:
        prompt += "\n\n--- LinkedIn Profile ---\n"
        if li_data.get("fullname"):
            prompt += f"Name: {li_data['fullname']}\n"
        if li_data.get("headline"):
            prompt += f"Headline: {li_data['headline']}\n"
        if li_data.get("location"):
            prompt += f"Location: {li_data['location']}\n"
        if li_data.get("email"):
            prompt += f"Email: {li_data['email']}\n"
        if li_data.get("about"):
            prompt += f"Summary: {li_data['about']}\n"
        for exp in li_data.get("experience", []):
            title = exp.get("title", exp.get("position", ""))
            company = exp.get("company", "")
            start = exp.get("start_date", exp.get("startDate", ""))
            end = exp.get("end_date", exp.get("endDate", "Present"))
            prompt += f"- {title} at {company} ({start}–{end})\n"
            if exp.get("description"):
                prompt += f"  {exp['description']}\n"
        for edu in li_data.get("education", []):
            degree = edu.get("degree_name", edu.get("degreeName", ""))
            field = edu.get("field_of_study", edu.get("fieldOfStudy", ""))
            school = edu.get("school", edu.get("schoolName", ""))
            prompt += f"- {degree} {field} @ {school}\n"
        for proj in li_data.get("projects", []):
            name = proj.get("name", "")
            desc = proj.get("description", "")
            if name:
                prompt += f"Project: {name}"
                if desc:
                    prompt += f" — {desc}"
                prompt += "\n"
        langs = [
            lang.get("language")
            for lang in li_data.get("languages", [])
            if lang.get("language")
        ]
        if langs:
            prompt += f"Languages: {', '.join(langs)}\n"

    for hf_entry in hf_profiles:
        hf_name, hf_info = ("", hf_entry) if isinstance(hf_entry, dict) else hf_entry
        prompt += (
            f"\n\n--- HuggingFace Profile: {hf_name} ---\n"
            if hf_name
            else "\n\n--- HuggingFace Profile ---\n"
        )
        for model in hf_info.get("models", []):
            prompt += (
                f"Model: {model.get('id', '')} — {model.get('downloads', 0)} downloads, "
                f"{model.get('likes', 0)} likes\n"
            )
        for dataset in hf_info.get("datasets", []):
            prompt += (
                f"Dataset: {dataset.get('id', '')} — {dataset.get('downloads', 0)} downloads, "
                f"{dataset.get('likes', 0)} likes\n"
            )
        for space in hf_info.get("spaces", []):
            prompt += f"Space: {space.get('id', '')} — {space.get('likes', 0)} likes\n"

    for orcid_entry in orcid_profiles:
        prompt += "\n\n--- ORCID Research Profile ---\n"
        if orcid_entry.get("name"):
            prompt += f"Name: {orcid_entry['name']}\n"
        if orcid_entry.get("employments"):
            prompt += "Affiliations:\n"
            for emp in orcid_entry["employments"]:
                prompt += (
                    f"- {emp.get('role', '')}, {emp.get('org', '')} "
                    f"({emp.get('start', '')}–{emp.get('end', '')})\n"
                )
        if orcid_entry.get("educations"):
            prompt += "Education:\n"
            for edu in orcid_entry["educations"]:
                prompt += f"- {edu.get('degree', '')}, {edu.get('org', '')} ({edu.get('year', '')})\n"
        if orcid_entry.get("works"):
            prompt += "Publications:\n"
            for work in orcid_entry["works"]:
                year = work.get("year", "")
                prompt += f"- {work.get('title', '')}"
                if year:
                    prompt += f" ({year})"
                prompt += "\n"

    prompt += "\n\n--- Additional User Information ---\n"
    prompt += (
        additional_info
        if additional_info and additional_info.strip()
        else "(No additional information provided)"
    )

    if resume_template:
        prompt += (
            "\n\n--- Resume Template Structure ---\n"
            "Use this EXACT structure but replace ALL {{PLACEHOLDER}} fields with the user's real data. "
            "Do NOT output unfilled placeholders. Do NOT copy the template verbatim.\n"
        )
        prompt += resume_template

    if job_description and job_description.strip():
        prompt += f"\n\n--- Target Job Description ---\n{job_description}\n"
        prompt += "Match keywords naturally. Reorder to highlight relevant items. Never fabricate.\n"

    if ats_feedback:
        prompt += (
            "\n\n--- PARSEABILITY ISSUES IN PREVIOUS VERSION ---\n"
            "The compiled PDF failed these machine checks. You MUST address "
            "every one of them in the LaTeX you produce now:\n"
            f"{ats_feedback}\n"
            "Rules: keep the same factual content — fix formatting, fonts, "
            "structure, and wording style only. Never invent new facts.\n"
        )

    section_order = (
        "Contact → Summary → Experience → Projects → Skills → Education"
        if priority == "experience"
        else "Contact → Summary → Projects → Experience → Skills → Education"
        if priority == "projects"
        else "Contact → Summary → Experience → Projects → Skills → Education (equal bullets 50/50 between experience and projects)"
    )

    template_instruction = (
        "Use the resume_template structure above — replace ALL placeholder content with real user data. Do NOT leave any placeholder unfilled."
        if resume_template
        else "Use standard LaTeX resume structure with \\documentclass[11pt,a4paper]{article}."
    )

    prompt += f"""

--- End of Information ---

FORMAT INSTRUCTIONS:
1. Output a COMPLETE, compilable LaTeX document — no code fences, no markdown anywhere.
2. {template_instruction}
3. Section order: {section_order}
4. Contact header (centered):
   {{\\LARGE \\textbf{{Full Name}}}}\\\\[3pt]
   \\href{{mailto:email}}{{email}} | phone | city | \\href{{linkedin_url}}{{LinkedIn}} | \\href{{github_url}}{{GitHub}}
   (Only include fields that exist in the data above)
5. Escape all special chars: \\& \\% \\_ \\# \\$ \\{{ \\}}
6. Dates: use \\hfill on same line as employer/title
7. Bullets: \\begin{{itemize}}[nosep,leftmargin=*,topsep=1pt] ... \\end{{itemize}}
8. Omit any field or section for which no data was provided — never write N/A or placeholders
9. Every section MUST contain real content — \\begin{{document}} must NOT be empty
10. Target exactly 1 page — cut bullets if needed

Generate the complete LaTeX resume now:"""

    return prompt
