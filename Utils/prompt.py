import re

with open('../template.md', 'r') as f:
    TEMPLATE_STRUCTURE = f.read()

def extract_contact_info(text: str) -> dict:

    info = {
        "name": "",
        "email": "",
        "phone": "",
        "location": "",
        "linkedin": "",
        "github": ""
    }

    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        info["email"] = email_match.group(0)

    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    linkedin_match = re.search(r'linkedin\.com/in/([A-Za-z0-9-]+)', text)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(1)

    return info



def build_user_prompt(github_username: str, readme_content: str, additional_info: str, priority: str) -> str:

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
    prompt += readme_content if readme_content and readme_content.strip() else "(No GitHub profile content available)"

    prompt += "\n\n--- Additional User Information ---\n"
    prompt += additional_info if additional_info and additional_info.strip() else "(No additional information provided)"

    prompt += f"""

--- End of Information ---

FORMAT INSTRUCTIONS:
1. Use this structure as reference:
{TEMPLATE_STRUCTURE}

2. Section priority based on "{priority}":
   {"Experience → Projects → Skills → Education" if priority == "experience" else "Projects → Experience → Skills → Education"}

3. Contact line format (use | separator):
   email | phone | location | LinkedIn: username | GitHub: username
   (If any field is missing, omit it entirely)

4. Use ONLY these markdown elements:
   - # for name (only at top)
   - ## for section headers
   - **bold** for job titles, companies, project names
   - - for bullet points
   - | for inline separators

5. NO HTML, NO icons, NO special formatting

6. Maximum 35 lines of content - be selective

7. Copy exact details from the information above - no generic filler

Generate the resume now:"""

    return prompt