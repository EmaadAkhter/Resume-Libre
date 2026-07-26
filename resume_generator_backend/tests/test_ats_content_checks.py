"""Pure-string unit tests for the ats-checker v2 checks (content, contact,
and file categories) plus the category field itself. No PDFs, no client —
every check here operates on plain strings or numbers."""

from ats.checks import (
    all_caps_lines,
    broken_links,
    bullet_density,
    buzzwords,
    contact_info,
    date_format_consistency,
    duplicate_bullets,
    encoding_sanity,
    encrypted_pdf,
    file_size,
    filename_check,
    first_person,
    hyphenation_breaks,
    images,
    long_bullets,
    multiple_emails,
    orphan_headings,
    page_count,
    quantified_bullets,
    repeated_verbs,
    scanned_pdf,
)
from ats.thresholds import BULLET_DENSITY_WARN, QUANTIFIED_BULLETS_INFO

BULLETS = """Experience
- Built the API gateway used by 40 services.
- Led migration to Kubernetes, cutting costs 30%.
- Shipped the billing dashboard to 2,000 users.
"""

PROSE = """Summary
I am an engineer who does many things across the stack.
Responsibilities included maintaining several internal services.
There were also numerous meetings and documents to write.
Everything was handled with great care and attention over the years.
"""


# ── bullet-density ───────────────────────────────────────────────────


def test_bullet_density_passes_with_enough_bullets():
    check = bullet_density(BULLETS)
    assert check["status"] == "pass"
    assert check["metric"]["kind"] == "ratio"
    assert check["metric"]["warn_below"] == BULLET_DENSITY_WARN
    assert check["metric"]["value"] == 0.75


def test_bullet_density_warns_on_prose_walls():
    check = bullet_density(PROSE)
    assert check["status"] == "warn"
    assert "prose" in check["reason"]
    assert "bullet points" in check["fix"]
    assert check["metric"]["value"] == 0.0


def test_bullet_density_empty_text_passes():
    check = bullet_density("")
    assert check["status"] == "pass"
    assert "no bullets detected" in check["reason"].lower()
    assert "metric" not in check


def test_bullet_density_counts_all_marker_styles():
    text = "• one thing\n– another thing\n* third thing\n\\item fourth thing\n"
    assert bullet_density(text)["metric"]["value"] == 1.0


# ── quantified-bullets ───────────────────────────────────────────────


def test_quantified_bullets_passes_when_numbers_present():
    check = quantified_bullets(BULLETS)
    assert check["status"] == "pass"
    assert check["metric"]["warn_below"] == QUANTIFIED_BULLETS_INFO


def test_quantified_bullets_info_lists_unquantified_samples():
    text = (
        "- Improved the deployment process\n"
        "- Enhanced the monitoring stack\n"
        "- Reworked the onboarding documentation\n"
    )
    check = quantified_bullets(text)
    assert check["status"] == "info"
    assert check["informational"] is True
    assert "Improved the deployment process" in check["reason"]
    # at most two samples listed
    assert "Reworked the onboarding" not in check["reason"]
    assert "Add numbers" in check["fix"]


def test_quantified_bullets_omitted_below_three_bullets():
    assert quantified_bullets("- Improved things\n- Fixed stuff\n") is None
    assert quantified_bullets("no bullets at all") is None


def test_quantified_bullets_counts_percent_and_dollar():
    text = "- Cut costs by a lot $\n- Grew revenue %\n- Did something else\n"
    assert quantified_bullets(text)["metric"]["value"] > 0.6


# ── long-bullets ─────────────────────────────────────────────────────


def test_long_bullets_pass_when_concise():
    assert long_bullets(BULLETS)["status"] == "pass"


def test_long_bullets_info_names_worst_truncated():
    rambling = "- " + " ".join(f"word{i}" for i in range(40))
    check = long_bullets(rambling + "\n- Short one\n")
    assert check["status"] == "info"
    assert check["informational"] is True
    assert "word0" in check["reason"]
    assert "…" in check["reason"]  # truncated snippet


# ── repeated-verbs ───────────────────────────────────────────────────


def test_repeated_verbs_pass_with_variety():
    assert repeated_verbs(BULLETS)["status"] == "pass"


def test_repeated_verbs_info_names_verb_and_count():
    text = (
        "- Built the API\n- built the pipeline\n"
        "- Built the dashboard\n- Built the CLI\n"
    )
    check = repeated_verbs(text)
    assert check["status"] == "info"
    assert '"Built" starts 4 bullets' in check["reason"]
    assert "vary your action verbs" in check["reason"]


# ── first-person ─────────────────────────────────────────────────────


def test_first_person_warns_on_pronouns():
    check = first_person("I led my team and they reported to me.")
    assert check["status"] == "warn"
    assert "first-person" in check["reason"]


def test_first_person_passes_on_implied_voice():
    assert first_person("Led the team. Shipped the product.")["status"] == "pass"


def test_first_person_ignores_mysql_and_io():
    assert first_person("Tuned MySQL and disk I/O throughput.")["status"] == "pass"


# ── buzzwords ────────────────────────────────────────────────────────


def test_buzzwords_info_lists_hits():
    check = buzzwords("A passionate team player driving synergy.")
    assert check["status"] == "info"
    assert check["informational"] is True
    assert "team player" in check["reason"]
    assert "synergy" in check["reason"]


def test_buzzwords_pass_when_clean():
    assert buzzwords("Built an event pipeline in Go.")["status"] == "pass"


# ── all-caps-lines ───────────────────────────────────────────────────


def test_all_caps_warns_past_tolerance():
    text = (
        "BUILT THE WHOLE PLATFORM ALONE\nSHIPPED EVERYTHING FAST\n"
        "MANAGED ALL THE SERVERS\n"
    )
    check = all_caps_lines(text)
    assert check["status"] == "warn"
    assert "ALL CAPS" in check["reason"]


def test_all_caps_ignores_section_headers():
    text = "EXPERIENCE\nEDUCATION\nSKILLS\nPROJECTS\nnormal body line\n"
    assert all_caps_lines(text)["status"] == "pass"


def test_all_caps_tolerates_two_lines():
    assert (
        all_caps_lines("JOHN DOE\nSAN FRANCISCO, CA\nbody text\n")["status"] == "pass"
    )


# ── duplicate-bullets ────────────────────────────────────────────────


def test_duplicate_bullets_warn_names_duplicate():
    text = "- Built the API\n- Led the team\n-   built  the API\n"
    check = duplicate_bullets(text)
    assert check["status"] == "warn"
    assert "built" in check["reason"].lower()
    assert "2 times" in check["reason"]


def test_duplicate_bullets_pass_when_distinct():
    assert duplicate_bullets(BULLETS)["status"] == "pass"


# ── date-format-consistency ──────────────────────────────────────────


def test_date_formats_warn_names_both_styles():
    check = date_format_consistency("Jan 2020 - Mar 2021\nthen 04/2022 onward")
    assert check["status"] == "warn"
    assert "Mon YYYY" in check["reason"]
    assert "MM/YYYY" in check["reason"]


def test_date_formats_pass_single_style():
    assert date_format_consistency("Jan 2020 - Mar 2021")["status"] == "pass"
    assert date_format_consistency("2021-03 to 2022-11")["status"] == "pass"
    assert date_format_consistency("no dates at all")["status"] == "pass"


# ── hyphenation-breaks ───────────────────────────────────────────────


def test_hyphenation_warns_past_tolerance():
    text = "developed micro-\nservices and infra-\nstructure with moni-\ntoring"
    check = hyphenation_breaks(text)
    assert check["status"] == "warn"
    assert "split across lines" in check["reason"]


def test_hyphenation_tolerates_a_couple():
    assert (
        hyphenation_breaks("micro-\nservices once, infra-\nstructure twice")["status"]
        == "pass"
    )


# ── orphan-headings ──────────────────────────────────────────────────


def test_orphan_heading_followed_by_heading_warns():
    check = orphan_headings("Skills\nEducation\nB.S. in CS, 2019\n")
    assert check["status"] == "warn"
    assert "Skills" in check["reason"]


def test_orphan_heading_at_end_of_text_warns():
    check = orphan_headings("Experience\n- Built things\nProjects\n")
    assert check["status"] == "warn"
    assert "Projects" in check["reason"]


def test_orphan_headings_pass_when_sections_filled():
    text = "Experience\n- Built things\nEducation\nB.S. in CS, 2019\n"
    assert orphan_headings(text)["status"] == "pass"


def test_inline_header_word_is_not_an_orphan():
    # "Skills: Python" is a filled line, not a bare heading.
    assert orphan_headings("Skills: Python, SQL\nEducation\nB.S.\n")["status"] == "pass"


# ── multiple-emails ──────────────────────────────────────────────────


def test_multiple_emails_warn_lists_addresses():
    check = multiple_emails("a@x.com somewhere and b@y.com elsewhere")
    assert check["status"] == "warn"
    assert "a@x.com" in check["reason"]
    assert "b@y.com" in check["reason"]
    assert "first email" in check["reason"]


def test_multiple_emails_pass_single_or_repeated():
    assert multiple_emails("a@x.com and again A@X.com")["status"] == "pass"
    assert multiple_emails("no emails here")["status"] == "pass"


# ── broken-links ─────────────────────────────────────────────────────


def test_broken_links_warns_on_linebreak_split():
    check = broken_links("https://linkedin.com/in/joh\nndoe-profile")
    assert check["status"] == "warn"
    assert "split" in check["reason"]


def test_broken_links_warns_on_dot_gap():
    assert broken_links("https://github. com/janedoe")["status"] == "warn"


def test_broken_links_pass_on_intact_urls():
    assert broken_links("https://github.com/janedoe is my profile")["status"] == "pass"


# ── file-size ────────────────────────────────────────────────────────


def test_file_size_pass_under_cap():
    check = file_size(1024 * 1024)
    assert check["status"] == "pass"
    assert check["metric"] == {
        "kind": "band",
        "value": 1.0,
        "low": 0,
        "high": 2,
        "unit": "MB",
    }


def test_file_size_warns_over_two_megabytes():
    check = file_size(3 * 1024 * 1024)
    assert check["status"] == "warn"
    assert "cap uploads at 2" in check["reason"]
    assert check["metric"]["value"] == 3.0


# ── encrypted-pdf ────────────────────────────────────────────────────


def test_encrypted_pdf_statuses():
    assert encrypted_pdf(False)["status"] == "pass"
    check = encrypted_pdf(True)
    assert check["status"] == "fail"
    assert "protected" in check["reason"]


# ── filename ─────────────────────────────────────────────────────────


def test_filename_clean_passes():
    assert filename_check("JohnDoe_Backend.pdf")["status"] == "pass"


def test_filename_messy_patterns_are_info():
    for name in (
        "resume.pdf",
        "resume.docx",
        "Untitled(1).pdf",
        "JohnDoe_final.pdf",
        "Copy_of_cv.pdf",
        "John Doe Resume.pdf",
    ):
        check = filename_check(name)
        assert check["status"] == "info", name
        assert check["informational"] is True
        assert "FirstLast_Role.pdf" in check["fix"]


def test_filename_copy_token_needs_boundaries():
    # "Copywriter" contains "copy" but is a real word, not a working-file tag.
    assert filename_check("Copywriter_Resume2025.pdf")["status"] == "pass"


# ── categories ───────────────────────────────────────────────────────


def test_new_checks_carry_their_category():
    assert bullet_density(BULLETS)["category"] == "content"
    assert quantified_bullets(BULLETS)["category"] == "content"
    assert multiple_emails("a@x.com b@y.com")["category"] == "contact"
    assert broken_links("text")["category"] == "contact"
    assert file_size(10)["category"] == "file"
    assert encrypted_pdf(True)["category"] == "file"
    assert filename_check("x.pdf")["category"] == "file"


def test_existing_checks_recategorized():
    assert scanned_pdf()["category"] == "extraction"
    assert images(0)["category"] == "layout"
    assert page_count(1)["category"] == "file"
    assert encoding_sanity("plain")["category"] == "typography"
    assert contact_info("a@x.com +1 555-123-4567")["category"] == "contact"
