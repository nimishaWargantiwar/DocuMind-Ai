"""
Hybrid retrieval combining semantic search (FAISS) and keyword search (BM25).
Supports reranking of results for better relevance.
"""

from __future__ import annotations

from typing import Optional
from langchain_core.documents import Document


class BM25Retriever:
    """Simple BM25 keyword retriever for hybrid search."""
    
    def __init__(self, documents: list[Document]):
        """Initialize with documents."""
        self.documents = documents
        self._build_index()
    
    def _build_index(self) -> None:
        """Build simple inverted index."""
        self.index: dict[str, list[int]] = {}
        
        for doc_idx, doc in enumerate(self.documents):
            words = doc.page_content.lower().split()
            for word in set(words):
                # Simple normalization
                word = word.strip(".,!?;:\"'()").lower()
                if len(word) > 2:  # Skip very short words
                    if word not in self.index:
                        self.index[word] = []
                    self.index[word].append(doc_idx)
    
    def retrieve(self, query: str, k: int = 3) -> list[Document]:
        """Retrieve top-k documents by keyword match."""
        query_words = query.lower().split()
        
        # Score documents by keyword overlap
        scores: dict[int, int] = {}
        for word in query_words:
            word = word.strip(".,!?;:\"'()").lower()
            if word in self.index:
                for doc_idx in self.index[word]:
                    scores[doc_idx] = scores.get(doc_idx, 0) + 1
        
        # Sort by score and return top-k
        if not scores:
            return []
        
        sorted_indices = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:k]
        return [self.documents[idx] for idx in sorted_indices]


class SimpleReranker:
    """Simple reranker based on query term overlap."""
    
    def __init__(self, llm=None):
        """Initialize reranker (LLM optional for advanced reranking)."""
        self.llm = llm
    
    def rerank(self, query: str, documents: list[Document], k: int = 5) -> list[Document]:
        """Rerank documents by relevance to query."""
        if not documents:
            return []
        
        # Score documents based on query term presence and position
        scores: list[tuple[float, int]] = []
        query_words = set(query.lower().split())
        
        for i, doc in enumerate(documents):
            content_lower = doc.page_content.lower()
            
            # Count query word matches weighted by position (earlier = better)
            score = 0.0
            for word in query_words:
                if word in content_lower:
                    # Weight by position
                    pos = content_lower.find(word)
                    max_pos_weight = 1.0
                    pos_weight = max_pos_weight * (1.0 - min(pos / len(content_lower), 0.9))
                    score += 1.0 + pos_weight
            
            scores.append((score, i))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        reranked = [documents[idx] for score, idx in scores[:k]]
        
        return reranked


class HybridRetriever:
    """Combines semantic search (FAISS) and keyword search (BM25)."""
    
    def __init__(self, vector_store, documents: list[Document]):
        """
        Initialize hybrid retriever.
        
        Args:
            vector_store: FAISS vector store for semantic search
            documents: All documents for BM25 indexing
        """
        self.vector_store = vector_store
        self.documents = documents
        self.bm25_retriever = BM25Retriever(documents)
        self.reranker = SimpleReranker()
    
    def retrieve(
        self,
        query: str,
        k: int = 4,
        use_bm25: bool = True,
        use_reranking: bool = True
    ) -> list[Document]:
        """
        Retrieve documents using hybrid approach.
        
        Args:
            query: Search query
            k: Number of results to return
            use_bm25: Include BM25 keyword search
            use_reranking: Rerank results
        
        Returns:
            Top-k most relevant documents
        """
        # Get semantic results from FAISS
        semantic_results = self.vector_store.similarity_search(query, k=k)
        
        # Get keyword results from BM25 (if enabled)
        if use_bm25:
            keyword_results = self.bm25_retriever.retrieve(query, k=k)
            
            # Combine results, removing duplicates while preserving order
            combined = []
            seen_content = set()
            
            for doc in semantic_results + keyword_results:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    combined.append(doc)
                    seen_content.add(content_hash)
            
            results = combined[:k * 2]  # Keep up to 2x more for reranking
        else:
            results = semantic_results
        
        # Rerank results (if enabled)
        if use_reranking and len(results) > k:
            results = self.reranker.rerank(query, results, k=k)
        
        return results[:k]
