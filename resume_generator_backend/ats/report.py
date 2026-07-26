"""Assemble the final checklist report. Deliberately no blended score."""


def build_report(filename, checks, extracted=None):
    body = {
        "filename": filename,
        "checks": checks,
        # Summary counts only pass/warn/fail; informational checks
        # (status "info", informational=True) are suggestions, never
        # counted as failures or warnings.
        "summary": {
            "passed": sum(1 for c in checks if c["status"] == "pass"),
            "warned": sum(1 for c in checks if c["status"] == "warn"),
            "failed": sum(1 for c in checks if c["status"] == "fail"),
        },
    }
    if extracted is not None:
        body["extracted"] = {k: v.model_dump() for k, v in extracted.items()}
    return body
