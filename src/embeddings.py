from __future__ import annotations

from functools import lru_cache

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:  # pragma: no cover - compatibility fallback
    try:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    except ImportError:  # pragma: no cover - older LangChain fallback
        from langchain.embeddings import HuggingFaceEmbeddings


@lru_cache(maxsize=1)
def load_embeddings() -> HuggingFaceEmbeddings:
    """Load and cache the local embedding model used for semantic search."""

    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
