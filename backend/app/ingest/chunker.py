"""Deterministic text chunking for datasheet ingestion."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedPage:
    page_number: int
    text: str


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    page_number: int | None


PAGE_MARKER_PATTERN = re.compile(r"^---\s*Page\s+(\d+)\s*---\s*$", re.IGNORECASE | re.MULTILINE)


def parse_page_marked_text(text: str) -> list[ParsedPage]:
    matches = list(PAGE_MARKER_PATTERN.finditer(text))
    if not matches:
        cleaned = text.strip()
        return [ParsedPage(page_number=1, text=cleaned)] if cleaned else []

    pages: list[ParsedPage] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        page_text = text[start:end].strip()
        if page_text:
            pages.append(ParsedPage(page_number=int(match.group(1)), text=page_text))
    return pages


def chunk_page_text(
    page: ParsedPage,
    *,
    max_chars: int = 800,
    overlap: int = 80,
) -> list[TextChunk]:
    text = page.text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [TextChunk(chunk_index=0, content=text, page_number=page.page_number)]

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    content=chunk_text,
                    page_number=page.page_number,
                ),
            )
            chunk_index += 1
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_document_text(text: str, *, max_chars: int = 800, overlap: int = 80) -> list[TextChunk]:
    pages = parse_page_marked_text(text)
    chunks: list[TextChunk] = []
    next_index = 0
    for page in pages:
        for page_chunk in chunk_page_text(page, max_chars=max_chars, overlap=overlap):
            chunks.append(
                TextChunk(
                    chunk_index=next_index,
                    content=page_chunk.content,
                    page_number=page_chunk.page_number,
                ),
            )
            next_index += 1
    return chunks
