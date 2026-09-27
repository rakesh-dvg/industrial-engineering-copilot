"""PDF text extraction for datasheet ingestion."""

from __future__ import annotations

import io

from pypdf import PdfReader

from app.ingest.chunker import ParsedPage


def extract_pdf_pages(content: bytes) -> list[ParsedPage]:
    reader = PdfReader(io.BytesIO(content))
    pages: list[ParsedPage] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(ParsedPage(page_number=index, text=text))
    return pages
