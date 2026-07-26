"""Assemble the final checklist report. Deliberately no blended score."""


def build_report(filename, checks):
    return {
        "filename": filename,
        "checks": checks,
        "summary": {
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "warned": sum(1 for c in checks if c["status"] == "warn"),
            "failed": sum(1 for c in checks if c["status"] == "fail"),
        },
    }
