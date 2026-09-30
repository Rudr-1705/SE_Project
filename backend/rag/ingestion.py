"""Document ingestion — parses PDF, DOCX, TXT files into text."""
import os
from pathlib import Path


def parse_pdf(file_path: str) -> list[dict]:
    """Parse PDF file into pages of text."""
    from PyPDF2 import PdfReader
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page": i + 1, "content": text.strip()})
    return pages


def parse_docx(file_path: str) -> list[dict]:
    """Parse DOCX file into paragraphs."""
    from docx import Document as DocxDocument
    doc = DocxDocument(file_path)
    paragraphs = []
    for i, para in enumerate(doc.paragraphs):
        if para.text.strip():
            paragraphs.append({
                "page": i + 1,
                "content": para.text.strip(),
                "style": para.style.name if para.style else "",
            })
    return paragraphs


def parse_txt(file_path: str) -> list[dict]:
    """Parse plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    return [{"page": 1, "content": content}]


def parse_document(file_path: str) -> list[dict]:
    """Route to appropriate parser based on file extension."""
    ext = Path(file_path).suffix.lower()
    parsers = {
        ".pdf": parse_pdf,
        ".docx": parse_docx,
        ".txt": parse_txt,
        ".md": parse_txt,
        ".csv": parse_txt,
    }
    parser = parsers.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file type: {ext}")
    return parser(file_path)
