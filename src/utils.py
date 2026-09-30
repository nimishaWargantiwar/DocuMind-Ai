from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from langchain_core.documents import Document


@dataclass(frozen=True)
class SourceReference:
    source: str
    page: int | None = None
    chunk: int | None = None


def clean_text(text: str) -> str:
    """Normalize extracted text so chunking and retrieval work more reliably."""

    text = text.replace("\x00", " ")
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def document_excerpt(text: str, max_length: int = 240) -> str:
    """Create a compact excerpt suitable for a source preview."""

    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 1].rstrip() + "…"


def unique_source_references(documents: Iterable[Document]) -> list[SourceReference]:
    """Deduplicate source references while preserving their original order."""

    seen: set[tuple[str, int | None, int | None]] = set()
    references: list[SourceReference] = []

    for document in documents:
        source = str(document.metadata.get("source", "Unknown source"))
        page_value = document.metadata.get("page")
        chunk_value = document.metadata.get("chunk_index")

        page = int(page_value) if isinstance(page_value, (int, float)) else None
        chunk = int(chunk_value) if isinstance(chunk_value, (int, float)) else None

        key = (source, page, chunk)
        if key in seen:
            continue

        seen.add(key)
        references.append(SourceReference(source=source, page=page, chunk=chunk))

    return references


def format_source_reference(reference: SourceReference) -> str:
    parts = [reference.source]
    if reference.page is not None:
        parts.append(f"Page {reference.page}")
    if reference.chunk is not None:
        parts.append(f"Chunk {reference.chunk}")
    return " — ".join(parts)
