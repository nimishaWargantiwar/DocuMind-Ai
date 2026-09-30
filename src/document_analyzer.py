"""
Document analysis for generating summaries and key information.
Uses LLM to extract grounded information from documents.
"""

from __future__ import annotations

from dataclasses import dataclass
from langchain_core.documents import Document


@dataclass(frozen=True)
class DocumentAnalysis:
    """Analysis results for a document."""
    summary: str
    key_points: list[str]
    entities: dict[str, list[str]]  # people, organizations, dates, technologies, etc.
    important_numbers: list[str]
    important_concepts: list[str]


def analyze_document_for_summary(chunks: list[Document], llm) -> str:
    """Generate a summary from document chunks."""
    if not chunks:
        return "No content to summarize."
    
    # Combine chunks for context window
    combined_text = "\n\n---\n\n".join([chunk.page_content for chunk in chunks[:10]])  # Top 10 chunks
    
    from langchain_core.prompts import PromptTemplate
    
    prompt = PromptTemplate(
        input_variables=["content"],
        template="""Based ONLY on the following document content, provide a comprehensive summary.
Do not add information from outside the document.
Keep the summary concise but complete (2-4 paragraphs).

Document content:
{content}

Summary:"""
    )
    
    chain = prompt | llm
    response = chain.invoke({"content": combined_text})
    
    return response.content if hasattr(response, "content") else str(response)


def analyze_document_for_key_points(chunks: list[Document], llm) -> list[str]:
    """Extract key points from document."""
    if not chunks:
        return []
    
    combined_text = "\n\n---\n\n".join([chunk.page_content for chunk in chunks[:10]])
    
    from langchain_core.prompts import PromptTemplate
    
    prompt = PromptTemplate(
        input_variables=["content"],
        template="""Based ONLY on the following document content, extract the 5-10 most important key points.
Do not add information from outside the document.
Format as a numbered list.

Document content:
{content}

Key Points:"""
    )
    
    chain = prompt | llm
    response = chain.invoke({"content": combined_text})
    
    text = response.content if hasattr(response, "content") else str(response)
    
    # Parse numbered list
    lines = text.split("\n")
    points = []
    for line in lines:
        line = line.strip()
        if line and any(line.startswith(f"{i}.") for i in range(1, 15)):
            # Remove numbering
            point = line.split(".", 1)[1].strip() if "." in line else line
            if point:
                points.append(point)
    
    return points if points else [text]


def analyze_document_for_entities(chunks: list[Document], llm) -> dict[str, list[str]]:
    """Extract named entities from document."""
    if not chunks:
        return {}
    
    combined_text = "\n\n---\n\n".join([chunk.page_content for chunk in chunks[:10]])
    
    from langchain_core.prompts import PromptTemplate
    
    prompt = PromptTemplate(
        input_variables=["content"],
        template="""Based ONLY on the following document content, extract important entities.
Do not add information from outside the document.
List them in categories separated by ||

Document content:
{content}

Extract and format as: PEOPLE: [list] || ORGANIZATIONS: [list] || DATES: [list] || TECHNOLOGIES: [list]"""
    )
    
    chain = prompt | llm
    response = chain.invoke({"content": combined_text})
    
    text = response.content if hasattr(response, "content") else str(response)
    
    entities = {
        "people": [],
        "organizations": [],
        "dates": [],
        "technologies": []
    }
    
    sections = text.split("||")
    for section in sections:
        section = section.strip()
        if ":" in section:
            key, values = section.split(":", 1)
            key = key.strip().lower()
            
            # Parse list format
            values_str = values.strip().strip("[]")
            items = [v.strip() for v in values_str.split(",") if v.strip()]
            
            if key in entities:
                entities[key] = items
    
    return entities
