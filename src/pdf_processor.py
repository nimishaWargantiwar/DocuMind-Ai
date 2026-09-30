from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from PyPDF2 import PdfReader
from langchain_core.documents import Document

from .utils import clean_text


@dataclass(frozen=True)
class PDFProcessingReport:
    filename: str
    page_count: int | None
    extracted_pages: int
    status: str
    message: str


def extract_pdf_documents(uploaded_files: Iterable) -> tuple[list[Document], list[PDFProcessingReport]]:
    """Extract page-level documents and processing status from uploaded PDFs."""

    page_documents: list[Document] = []
    reports: list[PDFProcessingReport] = []

    for uploaded_file in uploaded_files:
        filename = getattr(uploaded_file, "name", "uploaded.pdf")

        try:
            if hasattr(uploaded_file, "seek"):
                uploaded_file.seek(0)

            reader = PdfReader(uploaded_file)
            page_count = len(reader.pages)

            if page_count == 0:
                reports.append(
                    PDFProcessingReport(
                        filename=filename,
                        page_count=0,
                        extracted_pages=0,
                        status="empty",
                        message="This PDF does not contain any pages.",
                    )
                )
                continue

            extracted_pages = 0

            for page_number, page in enumerate(reader.pages, start=1):
                text = clean_text(page.extract_text() or "")
                if not text:
                    continue

                extracted_pages += 1
                page_documents.append(
                    Document(
                        page_content=text,
                        metadata={
                            "source": filename,
                            "page": page_number,
                        },
                    )
                )

            if extracted_pages == 0:
                reports.append(
                    PDFProcessingReport(
                        filename=filename,
                        page_count=page_count,
                        extracted_pages=0,
                        status="scanned",
                        message="No extractable text was found. This PDF may be scanned or image-only.",
                    )
                )
            else:
                reports.append(
                    PDFProcessingReport(
                        filename=filename,
                        page_count=page_count,
                        extracted_pages=extracted_pages,
                        status="processed",
                        message=f"Extracted text from {extracted_pages} of {page_count} pages.",
                    )
                )

        except Exception as exc:  # pragma: no cover - defensive guard for malformed PDFs
            reports.append(
                PDFProcessingReport(
                    filename=filename,
                    page_count=None,
                    extracted_pages=0,
                    status="error",
                    message=f"Could not read this PDF: {exc}",
                )
            )

    return page_documents, reports
