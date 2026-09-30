"""
Document management for handling multiple PDFs with stable identifiers.
Tracks document metadata, selections, and removal without re-processing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import hashlib


@dataclass(frozen=True)
class DocumentInfo:
    """Immutable document information with stable identifier."""
    doc_id: str
    filename: str
    page_count: int
    extracted_pages: int
    total_chunks: int
    status: str  # "processed", "scanned", "empty", "error"
    message: str
    
    def display_name(self) -> str:
        """Return display name with status indicator."""
        icon = {
            "processed": "✅",
            "scanned": "⚠️",
            "empty": "⚠️",
            "error": "❌",
        }.get(self.status, "📄")
        return f"{icon} {self.filename}"


@dataclass
class DocumentManager:
    """Manages document collection without re-processing."""
    documents: dict[str, DocumentInfo] = field(default_factory=dict)
    selected_doc_ids: set[str] = field(default_factory=set)
    
    @staticmethod
    def generate_doc_id(filename: str, page_count: int) -> str:
        """Generate stable document ID from filename and page count."""
        # Stable hash based on filename and page count
        key = f"{filename}:{page_count}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def add_document(
        self,
        filename: str,
        page_count: int,
        extracted_pages: int,
        total_chunks: int,
        status: str,
        message: str
    ) -> str:
        """Add a document and return its stable ID."""
        doc_id = self.generate_doc_id(filename, page_count)
        
        # Don't re-add if already exists
        if doc_id in self.documents:
            return doc_id
        
        doc_info = DocumentInfo(
            doc_id=doc_id,
            filename=filename,
            page_count=page_count,
            extracted_pages=extracted_pages,
            total_chunks=total_chunks,
            status=status,
            message=message
        )
        self.documents[doc_id] = doc_info
        return doc_id
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document. Return True if successful."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self.selected_doc_ids.discard(doc_id)
            return True
        return False
    
    def select_document(self, doc_id: str) -> bool:
        """Select a document for operations."""
        if doc_id in self.documents:
            self.selected_doc_ids.add(doc_id)
            return True
        return False
    
    def deselect_document(self, doc_id: str) -> None:
        """Deselect a document."""
        self.selected_doc_ids.discard(doc_id)
    
    def toggle_document(self, doc_id: str) -> bool:
        """Toggle selection of a document. Return new selection state."""
        if doc_id in self.documents:
            if doc_id in self.selected_doc_ids:
                self.deselect_document(doc_id)
                return False
            else:
                self.select_document(doc_id)
                return True
        return False
    
    def select_all(self) -> None:
        """Select all documents."""
        self.selected_doc_ids = set(self.documents.keys())
    
    def deselect_all(self) -> None:
        """Deselect all documents."""
        self.selected_doc_ids.clear()
    
    def clear_all(self) -> None:
        """Clear all documents."""
        self.documents.clear()
        self.selected_doc_ids.clear()
    
    def get_document(self, doc_id: str) -> Optional[DocumentInfo]:
        """Get document info by ID."""
        return self.documents.get(doc_id)
    
    def get_all_documents(self) -> list[DocumentInfo]:
        """Get all documents in order they were added."""
        return list(self.documents.values())
    
    def get_selected_documents(self) -> list[DocumentInfo]:
        """Get selected documents."""
        return [self.documents[doc_id] for doc_id in self.selected_doc_ids if doc_id in self.documents]
    
    def get_processed_documents(self) -> list[DocumentInfo]:
        """Get only successfully processed documents."""
        return [doc for doc in self.documents.values() if doc.status == "processed"]
    
    def count_documents(self) -> int:
        """Total document count."""
        return len(self.documents)
    
    def count_selected(self) -> int:
        """Selected document count."""
        return len(self.selected_doc_ids)
    
    def count_processed(self) -> int:
        """Processed document count."""
        return sum(1 for doc in self.documents.values() if doc.status == "processed")
    
    def has_selection(self) -> bool:
        """Check if any documents are selected."""
        return len(self.selected_doc_ids) > 0
