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

    prompt = f"""Format this information into a one-page, ATS-friendly resume in markdown.

PRIORITY: {priority.title()} first

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
        langs = [l.get("language") for l in linkedin_data.get("languages", []) if l.get("language")]
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
            "\n\n--- Resume Template Structure (use as reference for formatting) ---\n"
        )
        prompt += resume_template

    if job_description and job_description.strip():
        prompt += f"\n\n--- Target Job Description ---\n{job_description}\n"
        prompt += "Match keywords naturally. Reorder to highlight relevant items. Never fabricate.\n"

    prompt += f"""

--- End of Information ---

FORMAT INSTRUCTIONS:
1. Use this structure as reference:
{TEMPLATE_STRUCTURE}

2. {"IMPORTANT: If a resume template was provided above, follow its structure and formatting style closely while updating the content with the user's information." if resume_template else f'Section priority based on "{priority}":'}

3. Section priority based on "{priority}":
   {"Experience → Projects → Skills → Education" if priority == "experience" else "Projects → Experience → Skills → Education"}

4. Contact line format (use | separator):
   email | phone | location | LinkedIn: username | GitHub: username
   (If any field is missing, omit it entirely)

5. Use ONLY these markdown elements:
   - # for name (only at top)
   - ## for section headers
   - **bold** for job titles, companies, project names
   - - for bullet points
   - | for inline separators

6. NO HTML, NO icons, NO special formatting

7. Maximum 35 lines of content - be selective

8. Copy exact details from the information above - no generic filler

Generate the resume now:"""

    return prompt
