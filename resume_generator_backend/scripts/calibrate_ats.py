"""Calibration harness for the ATS parseability thresholds (issue #31).

Procedure:
1. Collect 25-30 real resumes covering the layout spectrum: single column,
   two column, tables, LaTeX exports, Word exports, and design-tool
   (Canva/Figma/InDesign) exports.
2. For each resume <stem>.pdf, create the ground truth <stem>.txt by
   opening the PDF in a viewer and copy-pasting its text top-to-bottom.
3. Label each resume in <stem>.label with a single word: "good" when a
   human judges the extracted text faithful to the ground truth, "bad"
   when it comes out scrambled, glued, or with missing content.
4. Put all three files per resume in a directory (default ./calibration,
   ignored by git) and run from resume_generator_backend/:

       python -m scripts.calibrate_ats [directory]

5. Read the per-file table, then adopt the suggested thresholds into
   ats/thresholds.py when the good/bad populations separate cleanly;
   otherwise collect more samples.

Uses only the stdlib plus the extractors already shipped with the app.
"""

import argparse
import difflib
import sys
from pathlib import Path

from ats.checks import _normalize
from ats.extractors import extract_pdf_pdfplumber, extract_pdf_pymupdf
from ats.thresholds import AGREEMENT_PASS, AGREEMENT_WARN, COMPLETENESS_PASS

_COLUMNS = (
    ("file", 24),
    ("label", 6),
    ("pl_ratio", 9),
    ("mu_ratio", 9),
    ("x_ratio", 8),
    ("pl_jacc", 8),
    ("mu_jacc", 8),
    ("x_jacc", 7),
)


def _ratio(text_a, text_b):
    return difflib.SequenceMatcher(None, _normalize(text_a), _normalize(text_b)).ratio()


def _jaccard(text_a, text_b):
    set_a = set(_normalize(text_a).split())
    set_b = set(_normalize(text_b).split())
    union = set_a | set_b
    return len(set_a & set_b) / len(union) if union else 1.0


def _collect(directory):
    rows = []
    for pdf_path in sorted(directory.glob("*.pdf")):
        txt_path = pdf_path.with_suffix(".txt")
        label_path = pdf_path.with_suffix(".label")
        if not txt_path.exists() or not label_path.exists():
            print(f"skipping {pdf_path.name}: missing .txt or .label sibling")
            continue
        label = label_path.read_text().strip().lower()
        if label not in ("good", "bad"):
            print(f"skipping {pdf_path.name}: label must be good|bad, got {label!r}")
            continue
        truth = txt_path.read_text()
        data = pdf_path.read_bytes()
        plumber = extract_pdf_pdfplumber(data)
        pymupdf = extract_pdf_pymupdf(data)
        rows.append(
            {
                "file": pdf_path.name,
                "label": label,
                "pl_ratio": _ratio(plumber, truth),
                "mu_ratio": _ratio(pymupdf, truth),
                "x_ratio": _ratio(plumber, pymupdf),
                "pl_jacc": _jaccard(plumber, truth),
                "mu_jacc": _jaccard(pymupdf, truth),
                "x_jacc": _jaccard(plumber, pymupdf),
            }
        )
    return rows


def _print_table(rows):
    header = "  ".join(name.ljust(width) for name, width in _COLUMNS)
    print(header)
    print("-" * len(header))
    for row in rows:
        cells = []
        for name, width in _COLUMNS:
            value = row[name]
            text = f"{value:.3f}" if isinstance(value, float) else str(value)
            cells.append(text.ljust(width))
        print("  ".join(cells))


def _suggest(rows, metric, label):
    """Midpoint threshold when good/bad populations separate on a metric."""
    good = [r[metric] for r in rows if r["label"] == "good"]
    bad = [r[metric] for r in rows if r["label"] == "bad"]
    if not good or not bad:
        print(f"{label}: need both good and bad samples to suggest a threshold")
        return
    if min(good) > max(bad):
        midpoint = (min(good) + max(bad)) / 2
        print(
            f"{label}: suggested threshold {midpoint:.3f} "
            f"(good >= {min(good):.3f}, bad <= {max(bad):.3f})"
        )
    else:
        print(f"{label}: no clean separation — collect more samples")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "directory",
        nargs="?",
        default="calibration",
        help="directory of <stem>.pdf + <stem>.txt + <stem>.label triples",
    )
    args = parser.parse_args(argv)
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"not a directory: {directory}")
        return 1

    rows = _collect(directory)
    if not rows:
        print("no usable samples found")
        return 1

    _print_table(rows)
    print()
    _suggest(rows, "x_ratio", "cross-extractor agreement ratio")
    _suggest(rows, "x_jacc", "cross-extractor word-set Jaccard")
    print()
    print("current thresholds (ats/thresholds.py):")
    print(f"  AGREEMENT_PASS    = {AGREEMENT_PASS}")
    print(f"  AGREEMENT_WARN    = {AGREEMENT_WARN}")
    print(f"  COMPLETENESS_PASS = {COMPLETENESS_PASS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
