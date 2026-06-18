from services.prompt import extract_contact_info, build_user_prompt


def test_extract_contact_info_finds_email():
    text = "Contact me at john@example.com for details"
    info = extract_contact_info(text)
    assert info["email"] == "john@example.com"


def test_extract_contact_info_finds_phone():
    text = "Call me at +1-234-567-8900"
    info = extract_contact_info(text)
    assert "234" in info["phone"]


def test_extract_contact_info_finds_linkedin():
    text = "Connect: https://linkedin.com/in/johndoe"
    info = extract_contact_info(text)
    assert info["linkedin"] == "johndoe"


def test_extract_contact_info_empty_text():
    info = extract_contact_info("")
    assert info["email"] == ""
    assert info["phone"] == ""
    assert info["linkedin"] == ""


def test_build_user_prompt_contains_github_username():
    prompt = build_user_prompt("octocat", "readme content", "extra info", "experience")
    assert "octocat" in prompt
    assert "readme content" in prompt
    assert "extra info" in prompt


def test_build_user_prompt_contains_priority():
    prompt = build_user_prompt("user", "readme", "info", "projects")
    assert "Projects" in prompt


def test_build_user_prompt_with_template():
    prompt = build_user_prompt("user", "readme", "info", "experience", "TEMPLATE CONTENT")
    assert "TEMPLATE CONTENT" in prompt
