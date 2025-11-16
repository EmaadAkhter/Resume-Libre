import re
def clean_markdown_output(resume: str) -> str:

    resume = re.sub(r'```(?:markdown|md)?', '', resume)

    resume = re.sub(r'<[^>]+>', '', resume)

    resume = re.sub(r':\w+:', '', resume)

    resume = re.sub(r'[\U00010000-\U0010ffff]', '', resume)

    resume = ''.join(char for char in resume if ord(char) < 127 or char in ['\n', '\t'])

    resume = re.sub(r' +', ' ', resume)

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
    if len(content_lines) > 35:
        print(f"Warning: {len(content_lines)} lines, trimming to 35")
        all_lines = result.split('\n')
        result = '\n'.join(all_lines[:45])

    return result