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
    resume_template: str = None,
    linkedin_data: dict = None,
    job_description: str = "",
) -> str:
    contact = extract_contact_info(additional_info + " " + readme_content)

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

    prompt += "\n\n--- GitHub Profile Content ---\n"
    prompt += (
        readme_content
        if readme_content and readme_content.strip()
        else "(No GitHub profile content available)"
    )

    if linkedin_data:
        prompt += "\n\n--- LinkedIn Profile ---\n"
        if linkedin_data.get("fullname"):
            prompt += f"Name: {linkedin_data['fullname']}\n"
        if linkedin_data.get("headline"):
            prompt += f"Headline: {linkedin_data['headline']}\n"
        if linkedin_data.get("location"):
            prompt += f"Location: {linkedin_data['location']}\n"
        if linkedin_data.get("email"):
            prompt += f"Email: {linkedin_data['email']}\n"
        if linkedin_data.get("about"):
            prompt += f"Summary: {linkedin_data['about']}\n"
        for exp in linkedin_data.get("experience", []):
            title = exp.get("title", exp.get("position", ""))
            company = exp.get("company", "")
            start = exp.get("start_date", exp.get("startDate", ""))
            end = exp.get("end_date", exp.get("endDate", "Present"))
            prompt += f"- {title} at {company} ({start}–{end})\n"
            if exp.get("description"):
                prompt += f"  {exp['description']}\n"
        for edu in linkedin_data.get("education", []):
            degree = edu.get("degree_name", edu.get("degreeName", ""))
            field = edu.get("field_of_study", edu.get("fieldOfStudy", ""))
            school = edu.get("school", edu.get("schoolName", ""))
            prompt += f"- {degree} {field} @ {school}\n"
        for proj in linkedin_data.get("projects", []):
            name = proj.get("name", "")
            desc = proj.get("description", "")
            if name:
                prompt += f"Project: {name}"
                if desc:
                    prompt += f" — {desc}"
                prompt += "\n"
        langs = [
            lang.get("language")
            for lang in linkedin_data.get("languages", [])
            if lang.get("language")
        ]
        if langs:
            prompt += f"Languages: {', '.join(langs)}\n"

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
