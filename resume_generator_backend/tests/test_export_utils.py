from services.export_utils import get_filename_base


def test_get_filename_base_extracts_name():
    md = "# John Doe\n## Experience\n..."
    assert get_filename_base(md) == "John_Doe"


def test_get_filename_base_no_heading():
    md = "Just some text without a heading"
    assert get_filename_base(md) == "resume"
