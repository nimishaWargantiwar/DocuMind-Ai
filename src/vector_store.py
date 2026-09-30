from __future__ import annotations

from dataclasses import dataclass

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(frozen=True)
class ChunkingResult:
    chunks: list[Document]
    chunk_count: int


def chunk_documents(
    page_documents: list[Document],
    *,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> ChunkingResult:
    """Split page-level documents into retrieval-friendly chunks."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
        length_function=len,
    )

    chunks: list[Document] = []

    for page_document in page_documents:
        page_chunks = splitter.create_documents(
            [page_document.page_content],
            metadatas=[page_document.metadata],
        )

        for chunk_index, chunk_document in enumerate(page_chunks, start=1):
            metadata = dict(chunk_document.metadata)
            metadata["chunk_index"] = chunk_index
            metadata["chunk_id"] = f"{metadata.get('source', 'document')}-p{metadata.get('page', 'NA')}-c{chunk_index}"

            chunks.append(
                Document(
                    page_content=chunk_document.page_content,
                    metadata=metadata,
                )
            )

    return ChunkingResult(chunks=chunks, chunk_count=len(chunks))


def build_vector_store(chunks: list[Document], embeddings) -> FAISS:
    """Create a FAISS index from chunked documents."""

    if not chunks:
        raise ValueError("No chunks were created from the uploaded PDFs.")

    return FAISS.from_documents(chunks, embeddings)
