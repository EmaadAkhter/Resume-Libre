"""Stage 1 — text extraction. PDFs get dual extraction (pdfplumber and
PyMuPDF) so downstream checks can compare the two; DOCX has a single
extractor and the agreement check auto-passes."""

import io

import docx
import fitz  # PyMuPDF
import pdfplumber


def extract_pdf_pdfplumber(data):
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def extract_pdf_pymupdf(data):
    with fitz.open(stream=data, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def extract_docx(data):
    """Return (text, table_count) from a DOCX in one pass."""
    document = docx.Document(io.BytesIO(data))
    text = "\n".join(p.text for p in document.paragraphs)
    return text, len(document.tables)
