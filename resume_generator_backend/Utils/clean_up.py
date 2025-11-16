import re


def clean_markdown_output(resume: str) -> str:

    resume = re.sub(r'```(?:markdown|md)?', '', resume)

    resume = re.sub(r'(?<!\[):(\w+):(?!\()', '', resume)

    resume = re.sub(r'[\U00010000-\U0010ffff]', '', resume)

    resume = re.sub(r' {2,}', ' ', resume)

    resume = re.sub(r'\n{3,}', '\n\n', resume)

    return resume.strip()


def validate_and_fix_format(resume: str) -> str:

    resume = clean_markdown_output(resume)
    lines = resume.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()

        if not line and not formatted_lines:
            continue

        if line.startswith('##'):
            if formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
            formatted_lines.append(line)
            continue

        formatted_lines.append(line)

    cleaned = []
    prev_blank = False
    for line in formatted_lines:
        if line == '':
            if not prev_blank:
                cleaned.append(line)
                prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    result = '\n'.join(cleaned)

    content_lines = [l for l in result.split('\n') if l.strip()]
    if len(content_lines) > 40:
        print(f"Warning: Resume has {len(content_lines)} content lines (recommended: 35-40)")

    return result


def validate_resume_quality(resume: str) -> dict:

    issues = []
    warnings = []

    if re.search(r'<[^>]+>', resume):
        issues.append("Resume contains HTML tags - these must be removed")

    if 'iconify' in resume.lower() or 'data-icon' in resume.lower():
        issues.append("Resume contains icon codes - use plain text instead")

    if 'http' in resume and not re.search(r'\[.*?\]\(http', resume):
        warnings.append("URLs found but not properly formatted as markdown links")

    if not re.search(r'\[.*?@.*?\]\(mailto:', resume):
        warnings.append("Email should be formatted as clickable link")

    generic_phrases = [
        'building applications',
        'developing solutions',
        'passionate about',
        'team player',
        'hard worker'
    ]
    for phrase in generic_phrases:
        if phrase.lower() in resume.lower():
            warnings.append(f"Found generic phrase: '{phrase}' - consider being more specific")

    content_lines = [l for l in resume.split('\n') if l.strip()]
    if len(content_lines) > 45:
        warnings.append(f"Resume has {len(content_lines)} lines - consider trimming to 35-40 for one page")

    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'line_count': len(content_lines)
    }