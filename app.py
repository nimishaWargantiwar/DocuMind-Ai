from __future__ import annotations

import os
import time
from typing import Any

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

from src.embeddings import load_embeddings
from src.pdf_processor import extract_pdf_documents
from src.rag_pipeline import build_pipeline
from src.utils import document_excerpt, format_source_reference, unique_source_references
from src.vector_store import build_vector_store, chunk_documents
from src.document_manager import DocumentManager, DocumentInfo


# ============================================================
# STATE MANAGEMENT
# ============================================================

def initialize_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("document_reports", [])
    st.session_state.setdefault("vector_store", None)
    st.session_state.setdefault("indexed_chunk_count", 0)
    st.session_state.setdefault("retrieved_chunk_count", 0)
    st.session_state.setdefault("last_error", None)
    st.session_state.setdefault("document_manager", DocumentManager())
    st.session_state.setdefault("processed_docs_ids", set())
    st.session_state.setdefault("current_workspace", "Chat")
    st.session_state.setdefault("api_key", os.getenv("OPENAI_API_KEY", ""))
    st.session_state.setdefault("retrieval_k", 4)
    st.session_state.setdefault("temperature", 0.2)
    st.session_state.setdefault("use_hybrid", False)


def build_chat_history(messages: list[dict[str, Any]]) -> list[HumanMessage | AIMessage]:
    history: list[HumanMessage | AIMessage] = []
    for message in messages:
        content = message.get("content", "")
        if message.get("role") == "user":
            history.append(HumanMessage(content=content))
        elif message.get("role") == "assistant":
            history.append(AIMessage(content=content))
    return history


def reset_documents() -> None:
    st.session_state.vector_store = None
    st.session_state.document_reports = []
    st.session_state.indexed_chunk_count = 0
    st.session_state.retrieved_chunk_count = 0
    st.session_state.messages = []
    st.session_state.last_error = None


def clear_conversation() -> None:
    st.session_state.messages = []
    st.session_state.retrieved_chunk_count = 0
    st.session_state.last_error = None


# ============================================================
# PDF PROCESSING
# ============================================================

def process_uploaded_documents(uploaded_files, retrieval_k: int) -> None:
    status = st.empty()
    status.info("🔄 Extracting text...")

    page_documents, reports = extract_pdf_documents(uploaded_files)
    st.session_state.document_reports = reports
    
    doc_manager = st.session_state.document_manager
    for report in reports:
        doc_id = doc_manager.add_document(
            filename=report.filename,
            page_count=report.page_count or 0,
            extracted_pages=report.extracted_pages,
            total_chunks=0,
            status=report.status,
            message=report.message
        )
        if report.status == "processed":
            st.session_state.processed_docs_ids.add(doc_id)

    if not page_documents:
        st.session_state.vector_store = None
        st.session_state.indexed_chunk_count = 0
        message = "No readable text found. Try a text-based PDF."
        st.session_state.last_error = message
        status.error(message)
        return

    status.info("🔄 Creating chunks...")
    chunk_result = chunk_documents(page_documents)

    if not chunk_result.chunks:
        st.session_state.vector_store = None
        st.session_state.indexed_chunk_count = 0
        message = "Could not create searchable chunks."
        st.session_state.last_error = message
        status.error(message)
        return

    status.info("🔄 Generating embeddings...")
    embeddings = load_embeddings()

    status.info("🔄 Building index...")
    try:
        st.session_state.vector_store = build_vector_store(chunk_result.chunks, embeddings)
        st.session_state.indexed_chunk_count = chunk_result.chunk_count
        st.session_state.retrieved_chunk_count = 0
        st.session_state.messages = []
        st.session_state.last_error = None
        status.success(f"✅ Ready: {chunk_result.chunk_count} chunks indexed")
    except Exception as exc:
        st.session_state.vector_store = None
        st.session_state.indexed_chunk_count = 0
        message = f"Could not build index: {exc}"
        st.session_state.last_error = message
        status.error(message)


# ============================================================
# CHAT COMPONENTS
# ============================================================

def render_sources(source_documents) -> None:
    """Render sources as numbered citations."""
    references = unique_source_references(source_documents)
    if not references:
        return

    st.markdown(
        """
        <div style="margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #E5E7EB;">
            <p style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #667085; margin: 0 0 0.75rem 0;">
                Sources
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    for i, reference in enumerate(references, 1):
        formatted = format_source_reference(reference)
        st.markdown(
            f"""
            <div style="display: flex; gap: 0.75rem; margin-bottom: 0.5rem; font-size: 0.9375rem; color: #111827;">
                <span style="font-weight: 600; flex-shrink: 0;">①</span> if {i}==1 else f"<span>{'②③④⑤⑥'[i-2] if i<=7 else i}</span>"
                <span>{formatted}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_evidence_section(source_documents) -> None:
    """Render expandable evidence with proper formatting."""
    if not source_documents:
        return

    with st.expander("📖 View evidence", expanded=False):
        for i, doc in enumerate(source_documents, 1):
            source = str(doc.metadata.get("source", "Document"))
            page = doc.metadata.get("page", "?")
            
            st.markdown(
                f"""
                <div style="margin-bottom: 1.5rem;">
                    <p style="font-size: 0.875rem; font-weight: 600; color: #667085; margin: 0 0 0.5rem 0;">
                        Source {i}: {source} · Page {page}
                    </p>
                    <blockquote style="border-left: 3px solid #4F46E5; padding-left: 1rem; margin: 0; color: #111827; font-style: italic; line-height: 1.6;">
                        {document_excerpt(doc.page_content, max_length=300)}
                    </blockquote>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_chat_message_user(content: str) -> None:
    """Render user message."""
    st.markdown(
        f"""
        <div style="margin: 1.5rem 0; padding: 1rem; background: #EEF2FF; border-left: 3px solid #4F46E5; border-radius: 0.375rem;">
            <p style="margin: 0; color: #111827; line-height: 1.6;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chat_message_assistant(content: str, sources=None) -> None:
    """Render assistant message."""
    st.markdown(
        f"""
        <div style="margin: 1.5rem 0;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                <span style="font-weight: 700; color: #111827;">✦</span>
                <span style="font-size: 0.875rem; font-weight: 600; color: #667085; text-transform: uppercase; letter-spacing: 0.05em;">DocuMind</span>
            </div>
            <div style="color: #111827; line-height: 1.8; font-size: 0.9375rem;">
                {content}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if sources:
        render_sources(sources)
        render_evidence_section(sources)


def render_chat_history() -> None:
    """Render conversation history."""
    for message in st.session_state.messages:
        if message.get("role") == "user":
            render_chat_message_user(message["content"])
        elif message.get("role") == "assistant":
            render_chat_message_assistant(message["content"], message.get("sources"))


# ============================================================
# WORKSPACE: CHAT
# ============================================================

def workspace_chat(uploaded_files) -> None:
    """Main chat workspace - refined layout."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Chat", doc_count)
    
    if st.session_state.vector_store is None:
        # Empty state with refined layout
        col_empty = st.container()
        with col_empty:
            st.markdown(
                """
                <div style="text-align: center; padding: 3rem 2rem; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border); margin: 1rem 0; line-height: 1.6;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem; line-height: 1;">📚</div>
                    <h2 style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin: 0 0 0.5rem 0;">
                        Understand your documents
                    </h2>
                    <p style="font-size: 0.95rem; color: var(--text-secondary); max-width: 450px; margin: 0 auto 1.5rem;">
                        Upload PDFs and ask questions. Get answers grounded in your documents.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        if uploaded_files:
            st.markdown("")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Process documents", use_container_width=True, key="process_btn"):
                    process_uploaded_documents(uploaded_files, st.session_state.retrieval_k)
                    st.rerun()
        else:
            st.markdown(
                """
                <div style="text-align: center; margin-top: 2rem; padding: 1.5rem; color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6;">
                    <p style="margin: 0;">📤 Use the file uploader above to get started</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    else:
        # Chat ready - refined layout
        st.markdown(
            f"""
            <div style="padding: 0.75rem 1rem; background: var(--bg-surface); border: 1px solid var(--border); border-radius: var(--radius-md); margin-bottom: 1.5rem; font-size: 0.875rem; color: var(--text-secondary); display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: var(--success); font-weight: 600;">✓</span>
                <span><strong>{st.session_state.indexed_chunk_count}</strong> chunks indexed</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Chat history with proper spacing
        render_chat_history()
        
        # Chat input area with proper spacing
        st.markdown("")
        st.markdown(
            """
            <div style="margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border);"></div>
            """,
            unsafe_allow_html=True,
        )
        
        question = st.chat_input("Ask anything about your documents...")
        
        if question:
            question = question.strip()
            if question:
                st.session_state.messages.append({"role": "user", "content": question})
                render_chat_message_user(question)
                
                try:
                    with st.spinner("🔍 Searching documents..."):
                        start_time = time.time()
                        pipeline = build_pipeline(
                            st.session_state.vector_store,
                            retrieval_k=st.session_state.retrieval_k,
                            api_key=st.session_state.api_key.strip() or None,
                            temperature=st.session_state.temperature,
                            use_hybrid_retrieval=st.session_state.use_hybrid,
                        )
                        result = pipeline.ask(question, build_chat_history(st.session_state.messages[:-1]))
                        response_time = time.time() - start_time
                    
                    st.session_state.retrieved_chunk_count = len(result.source_documents)
                    
                    # Track evaluation
                    if "evaluator" in st.session_state:
                        st.session_state.evaluator.evaluate_response(
                            question=question,
                            answer=result.answer,
                            retrieved_chunks=len(result.source_documents),
                            response_time=response_time
                        )
                    
                    assistant_message = {
                        "role": "assistant",
                        "content": result.answer,
                        "sources": result.source_documents,
                    }
                    st.session_state.messages.append(assistant_message)
                    
                    render_chat_message_assistant(result.answer, result.source_documents)
                
                except ValueError as ve:
                    st.error(str(ve))
                except Exception as exc:
                    st.error("Could not generate answer. Check your API key.")


# ============================================================
# WORKSPACE: DOCUMENTS
# ============================================================

def workspace_documents() -> None:
    """Documents library workspace - refined layout."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Documents", doc_count)
    
    if doc_count == 0:
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">No documents uploaded yet.</p>
                <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">Use the uploader in the sidebar to get started.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 1rem;">
                Your documents
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        for doc in doc_manager.get_all_documents():
            col1, col2 = st.columns([1, 0.08], gap="large")
            
            with col1:
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border: 1px solid var(--border); border-radius: var(--radius-md); background: var(--bg-surface); transition: all 0.15s ease;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1;">
                                <p style="margin: 0; font-weight: 600; color: var(--text-primary); font-size: 0.95rem;">
                                    📄 {doc.filename}
                                </p>
                                <p style="margin: 0.5rem 0 0 0; font-size: 0.8125rem; color: var(--text-secondary);">
                                    {doc.page_count} pages · {doc.total_chunks} chunks
                                </p>
                            </div>
                            <span style="font-size: 0.75rem; font-weight: 600; color: var(--success); background: var(--success-light); padding: 0.375rem 0.625rem; border-radius: var(--radius-sm); white-space: nowrap;">
                                ✓ Ready
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            with col2:
                if st.button("🗑️", key=f"del_doc_{doc.doc_id}", help="Delete", use_container_width=True):
                    doc_manager.remove_document(doc.doc_id)
                    st.rerun()


# ============================================================
# WORKSPACE: ANALYZE
# ============================================================

def workspace_analyze() -> None:
    """Document analysis workspace - refined layout."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Analyze", doc_count)
    
    if doc_count == 0:
        st.info("📤 Upload documents first to analyze them.")
        return
    
    if doc_manager.count_selected() == 0:
        st.info("📌 Select documents in the sidebar to analyze them.")
        return
    
    st.markdown(
        """
        <div style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 1rem;">
            Document analysis
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    selected_docs = doc_manager.get_selected_documents()
    doc_names = ", ".join([d.filename[:25] for d in selected_docs])
    st.markdown(
        f"<p style='font-size: 0.875rem; color: var(--text-secondary); margin: 0 0 1.5rem 0;'>📄 {doc_names}</p>",
        unsafe_allow_html=True,
    )
    
    tabs = st.tabs(["Summary", "Key Points", "Entities"])
    
    try:
        from src.rag_pipeline import _load_chat_model
        from src.document_analyzer import (
            analyze_document_for_summary,
            analyze_document_for_key_points,
            analyze_document_for_entities,
        )
        
        retriever = st.session_state.vector_store.as_retriever(search_kwargs={"k": 15})
        chunks = retriever.invoke("summary and analysis")
        llm = _load_chat_model(api_key=None, temperature=0.2)
        
        with tabs[0]:
            with st.spinner("Generating summary..."):
                summary = analyze_document_for_summary(chunks, llm)
                st.markdown(summary)
        
        with tabs[1]:
            with st.spinner("Extracting key points..."):
                points = analyze_document_for_key_points(chunks, llm)
                for i, point in enumerate(points, 1):
                    st.markdown(f"**{i}.** {point}")
        
        with tabs[2]:
            with st.spinner("Extracting entities..."):
                entities = analyze_document_for_entities(chunks, llm)
                for entity_type, items in entities.items():
                    if items:
                        st.markdown(f"**{entity_type.title()}**")
                        for item in items:
                            st.markdown(f"• {item}")
    
    except Exception as e:
        st.error(f"Analysis error: {str(e)[:100]}")


# ============================================================
# WORKSPACE: COMPARE
# ============================================================

def workspace_compare() -> None:
    """Document comparison workspace - refined layout."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Compare", doc_count)
    
    if doc_count < 2:
        st.info("📤 Upload at least 2 documents to compare them.")
        return
    
    st.markdown(
        """
        <div style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 1.5rem;">
            Select documents
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    docs = doc_manager.get_all_documents()
    doc_names = [d.filename for d in docs]
    
    col1, col2, col3 = st.columns([1, 0.5, 1], gap="large")
    
    with col1:
        st.markdown("<p style='font-size: 0.875rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 0.5rem 0;'>Document A</p>", unsafe_allow_html=True)
        doc_a = st.selectbox(
            "Document A",
            doc_names,
            key="doc_a",
            label_visibility="collapsed",
        )
    
    with col2:
        st.markdown("<p style='text-align: center; margin-top: 1.25rem;' >vs</p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<p style='font-size: 0.875rem; font-weight: 500; color: var(--text-secondary); margin: 0 0 0.5rem 0;'>Document B</p>", unsafe_allow_html=True)
        doc_b = st.selectbox(
            "Document B",
            [d for d in doc_names if d != doc_a],
            key="doc_b",
            label_visibility="collapsed",
        )
    
    st.markdown("")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("Compare documents", use_container_width=True, key="compare_btn"):
            st.info("Document comparison coming soon")


# ============================================================
# WORKSPACE: EVALUATION
# ============================================================

def workspace_evaluation() -> None:
    """RAG evaluation workspace - refined layout."""
    render_app_header("Evaluation")
    
    if "evaluator" not in st.session_state:
        from src.evaluator import RAGEvaluator
        st.session_state.evaluator = RAGEvaluator()
    
    evaluator = st.session_state.evaluator
    
    if not evaluator.results:
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border);">
                <p style="color: var(--text-secondary); margin: 0; font-size: 0.95rem;">No evaluation data yet.</p>
                <p style="color: var(--text-secondary); font-size: 0.875rem; margin: 0.5rem 0 0 0;">Metrics will appear after asking questions.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
    
    st.markdown(
        """
        <div style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 1.5rem;">
            Quality metrics
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    metrics = evaluator.compute_metrics()
    
    col1, col2, col3, col4 = st.columns(4, gap="medium")
    
    with col1:
        st.metric(
            "Evaluated",
            f"{metrics.questions_evaluated}",
            label_visibility="collapsed",
        )
    
    with col2:
        st.metric(
            "Retrieval",
            f"{metrics.retrieval_relevance:.0f}%",
            label_visibility="collapsed",
        )
    
    with col3:
        st.metric(
            "Answer relevance",
            f"{metrics.answer_relevance:.0f}%",
            label_visibility="collapsed",
        )
    
    with col4:
        st.metric(
            "Groundedness",
            f"{metrics.groundedness:.0f}%",
            label_visibility="collapsed",
        )
    
    st.markdown("")
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        if st.button("Reset metrics", use_container_width=True, key="reset_eval_btn"):
            evaluator.reset()
            st.rerun()


# ============================================================
# NAVIGATION
# ============================================================

def render_sidebar() -> None:
    """Render navigation sidebar - refined layout with app name and fixed button states."""
    with st.sidebar:
        # APP NAME AT TOP
        st.markdown(
            """
            <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid var(--border);">
                <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                    <span style="font-size: 1.125rem; font-weight: 800; color: var(--text-primary);">✦</span>
                    <span style="font-size: 1.125rem; font-weight: 800; color: var(--text-primary);">DocuMind AI</span>
                </div>
                <p style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; margin: 0.25rem 0 0 0;">
                    AI-Powered Document Intelligence
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # WORKSPACE LABEL
        st.markdown(
            """
            <div style="font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Workspace
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Navigation buttons with proper states
        workspaces = [
            ("💬", "Chat"),
            ("📚", "Documents"),
            ("🧠", "Analyze"),
            ("🔀", "Compare"),
            ("📊", "Evaluation"),
        ]
        
        for icon, name in workspaces:
            is_active = st.session_state.current_workspace == name
            
            # Create custom styled button for active/inactive states
            if is_active:
                btn_style = """
                <style>
                .nav-btn-active { 
                    background-color: var(--accent) !important; 
                    color: white !important;
                }
                .nav-btn-active:hover {
                    background-color: var(--accent-hover) !important;
                }
                </style>
                """
                st.markdown(btn_style, unsafe_allow_html=True)
            
            if st.button(
                f"{icon} {name}",
                key=f"ws_{name}",
                use_container_width=True,
                help=f"Go to {name}",
            ):
                st.session_state.current_workspace = name
                st.rerun()
        
        st.markdown("---")
        
        # DOCUMENT MANAGEMENT
        st.markdown(
            """
            <div style="font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Documents
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        doc_manager = st.session_state.document_manager
        doc_count = doc_manager.count_documents()
        
        if doc_count > 0:
            st.markdown(
                f"<p style='font-size: var(--text-xs); color: var(--text-secondary); margin: 0.5rem 0 0.75rem 0;'><strong>{doc_count}</strong> uploaded</p>",
                unsafe_allow_html=True,
            )
            
            for doc in doc_manager.get_all_documents():
                col1, col2 = st.columns([1, 0.2], gap="small")
                with col1:
                    is_selected = st.checkbox(
                        doc.filename,
                        value=doc.doc_id in doc_manager.selected_doc_ids,
                        key=f"sel_{doc.doc_id}",
                        label_visibility="collapsed",
                    )
                    if is_selected:
                        doc_manager.select_document(doc.doc_id)
                    else:
                        doc_manager.deselect_document(doc.doc_id)
                    st.caption(doc.filename)
        else:
            st.caption("No documents")
        
        st.markdown("---")
        
        # SETTINGS
        st.markdown(
            """
            <div style="font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Settings
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        with st.expander("⚙️ Advanced", expanded=False):
            st.markdown("<p style='font-size: var(--text-xs); font-weight: 600; color: var(--text-secondary); margin: 0 0 0.5rem 0;'>LLM Configuration</p>", unsafe_allow_html=True)
            
            st.session_state.api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.api_key,
                help="Leave blank to use GROQ_API_KEY",
                placeholder="sk-...",
            )
            
            st.session_state.retrieval_k = st.slider(
                "Retrieved chunks",
                min_value=2,
                max_value=8,
                value=st.session_state.retrieval_k,
                help="More context = slower",
            )
            
            st.session_state.use_hybrid = st.checkbox(
                "Hybrid retrieval",
                value=st.session_state.use_hybrid,
                help="Combine semantic + keyword",
            )
            
            st.session_state.temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.05,
                help="0=factual, 1=creative",
            )
        
        st.markdown("---")
        
        # STATUS
        st.markdown(
            """
            <div style="font-size: var(--text-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Status
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        groq_ok = bool(os.getenv("GROQ_API_KEY"))
        openai_ok = bool(st.session_state.api_key.strip() or os.getenv("OPENAI_API_KEY"))
        
        if groq_ok or openai_ok:
            st.success("✓ LLM ready")
        else:
            st.warning("⚠ Configure API key")


def render_app_header(workspace: str, document_count: int = 0) -> None:
    """Render workspace header - refined styling."""
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border); margin-bottom: 1.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary);">
                    {workspace}
                </span>
            </div>
            {f'<div style="color: var(--text-secondary); font-size: 0.875rem;">📄 {document_count}</div>' if document_count > 0 else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_styles() -> None:
    """Render refined color polish pass - sophisticated indigo/blue palette with subtle tinted backgrounds."""
    st.markdown(
        """
        <style>
            /* ===== DESIGN TOKENS - COLOR POLISH PASS ===== */
            :root {
                /* MAIN BACKGROUNDS - Subtle blue-tinted off-white */
                --bg-primary: #F8F9FC;
                --bg-surface: #FFFFFF;
                --bg-subtle: #F5F7FA;
                --bg-accent-light: #F0F4FF;
                
                /* SIDEBAR - Slightly distinct cool tint */
                --bg-sidebar: #F9FAFB;
                
                /* TEXT COLORS - Navy and blue-gray hierarchy */
                --text-primary: #0F172A;
                --text-secondary: #475569;
                --text-tertiary: #94A3B8;
                --text-muted: #CBD5E1;
                
                /* PRIMARY BRAND COLOR - Professional indigo */
                --accent: #4F46E5;
                --accent-hover: #4338CA;
                --accent-dark: #312E81;
                --accent-light: #F0F4FF;
                --accent-lighter: #F5F8FF;
                
                /* BORDERS - Subtle blue-gray tinted */
                --border: #E2E8F0;
                --border-light: #F1F5F9;
                --border-accent: #DDD6FE;
                
                /* STATUS COLORS - Soft semantic colors */
                --success: #22C55E;
                --success-light: #ECFDF5;
                --warning: #F59E0B;
                --warning-light: #FFFBEB;
                --error: #EF4444;
                --error-light: #FEF2F2;
                --info: #3B82F6;
                --info-light: #EFF6FF;
                
                /* SPACING SYSTEM */
                --spacing-xs: 0.25rem;
                --spacing-sm: 0.5rem;
                --spacing-md: 1rem;
                --spacing-lg: 1.5rem;
                --spacing-xl: 2rem;
                --spacing-2xl: 3rem;
                
                /* BORDER RADIUS */
                --radius-sm: 0.375rem;
                --radius-md: 0.5rem;
                --radius-lg: 0.75rem;
                
                /* FONT SIZING */
                --text-xs: 0.75rem;
                --text-sm: 0.875rem;
                --text-base: 1rem;
                --text-lg: 1.125rem;
                --text-xl: 1.25rem;
                --text-2xl: 1.5rem;
                --text-3xl: 1.875rem;
            }
            
            /* ===== GLOBAL STYLES ===== */
            * {
                box-sizing: border-box;
            }
            
            body {
                background-color: var(--bg-primary);
                color: var(--text-primary);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
            }
            
            .main {
                background-color: var(--bg-primary);
            }
            
            .block-container {
                max-width: 1000px !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                padding-top: 1.5rem !important;
                padding-bottom: 2rem !important;
                margin-left: auto !important;
                margin-right: auto !important;
            }
            
            /* ===== TYPOGRAPHY ===== */
            h1, h2, h3, h4, h5, h6 {
                color: var(--text-primary) !important;
                font-weight: 700 !important;
                letter-spacing: -0.01em !important;
                margin-bottom: var(--spacing-md) !important;
            }
            
            h1 {
                font-size: var(--text-3xl) !important;
                margin-bottom: var(--spacing-lg) !important;
                color: var(--text-primary) !important;
            }
            
            h2 {
                font-size: var(--text-2xl) !important;
                margin-bottom: var(--spacing-md) !important;
                color: var(--text-primary) !important;
            }
            
            h3 {
                font-size: var(--text-xl) !important;
                margin-bottom: var(--spacing-md) !important;
                color: var(--text-primary) !important;
            }
            
            h4 {
                font-size: var(--text-lg) !important;
                margin-bottom: var(--spacing-sm) !important;
                color: var(--text-primary) !important;
            }
            
            p {
                color: var(--text-primary) !important;
                line-height: 1.6 !important;
                margin-bottom: var(--spacing-md) !important;
            }
            
            /* ===== MARKDOWN ===== */
            .stMarkdown {
                color: var(--text-primary) !important;
            }
            
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
                color: var(--text-primary) !important;
                font-weight: 700 !important;
            }
            
            .stMarkdown p {
                color: var(--text-primary) !important;
                line-height: 1.6 !important;
            }
            
            .stMarkdown strong {
                font-weight: 600 !important;
                color: var(--text-primary) !important;
            }
            
            /* ===== SIDEBAR - Color Polish ===== */
            section[data-testid="stSidebar"] {
                background-color: var(--bg-sidebar) !important;
                border-right: 1px solid var(--border) !important;
                padding: var(--spacing-md) !important;
            }
            
            section[data-testid="stSidebar"] .block-container {
                padding: 0 !important;
                max-width: 100% !important;
            }
            
            section[data-testid="stSidebar"] * {
                color: var(--text-primary) !important;
            }
            
            section[data-testid="stSidebar"] h1, 
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3 {
                margin-top: 0 !important;
            }
            
            /* Sidebar app name with brand color accent */
            section[data-testid="stSidebar"] > div > div > div:first-child .stMarkdown {
                margin-bottom: 1rem !important;
                padding-bottom: 1rem !important;
                border-bottom: 1px solid var(--border) !important;
            }
            
            /* ===== BUTTONS - Color Hierarchy ===== */
            .stButton button {
                background-color: var(--bg-surface) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border) !important;
                font-weight: 600 !important;
                font-size: var(--text-sm) !important;
                padding: 0.625rem 1.25rem !important;
                height: 2.25rem !important;
                border-radius: var(--radius-md) !important;
                letter-spacing: 0 !important;
                text-transform: none !important;
                transition: all 0.15s ease !important;
                cursor: pointer !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                white-space: nowrap !important;
                line-height: 1 !important;
            }
            
            .stButton button:hover:not(:disabled) {
                background-color: var(--bg-subtle) !important;
                border-color: var(--accent) !important;
                color: var(--accent) !important;
                transform: translateY(-1px) !important;
            }
            
            .stButton button:active:not(:disabled) {
                transform: translateY(0) !important;
                background-color: var(--bg-surface) !important;
            }
            
            .stButton button:disabled {
                background-color: var(--border-light) !important;
                color: var(--text-tertiary) !important;
                border-color: var(--border) !important;
                cursor: not-allowed !important;
            }
            
            /* SIDEBAR BUTTONS - Navigation with color polish */
            section[data-testid="stSidebar"] .stButton button {
                background-color: transparent !important;
                color: var(--text-secondary) !important;
                border: 1px solid transparent !important;
                font-weight: 600 !important;
                transition: all 0.2s ease !important;
            }
            
            section[data-testid="stSidebar"] .stButton button:hover {
                background-color: var(--accent-light) !important;
                color: var(--accent) !important;
                border-color: transparent !important;
            }
            
            /* SECONDARY BUTTONS */
            .stButton button[data-testid="baseButton-secondary"] {
                background-color: var(--bg-surface) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border) !important;
            }
            
            .stButton button[data-testid="baseButton-secondary"]:hover:not(:disabled) {
                background-color: var(--bg-subtle) !important;
                border-color: var(--accent) !important;
                color: var(--accent) !important;
                box-shadow: none !important;
            }
            
            /* ===== INPUT FIELDS - Color Polish ===== */
            .stTextInput > div > div > input,
            .stTextArea > div > div > textarea,
            .stSelectbox > div > div > select,
            .stNumberInput > div > div > input {
                background-color: var(--bg-surface) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                font-size: var(--text-sm) !important;
                padding: 0.5rem 0.75rem !important;
                line-height: 1.5 !important;
                transition: border-color 0.15s ease, box-shadow 0.15s ease !important;
            }
            
            .stTextInput > div > div > input::placeholder,
            .stTextArea > div > div > textarea::placeholder {
                color: var(--text-tertiary) !important;
            }
            
            .stTextInput > div > div > input:focus,
            .stTextArea > div > div > textarea:focus,
            .stSelectbox > div > div > select:focus,
            .stNumberInput > div > div > input:focus {
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 3px var(--accent-light) !important;
                outline: none !important;
                background-color: var(--bg-accent-lighter) !important;
            }
            
            /* ===== CHAT INPUT ===== */
            .stChatInput input {
                background-color: var(--bg-surface) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-md) !important;
                font-size: var(--text-sm) !important;
                padding: 0.75rem 1rem !important;
                line-height: 1.5 !important;
            }
            
            .stChatInput input::placeholder {
                color: var(--text-tertiary) !important;
            }
            
            .stChatInput input:focus {
                border-color: var(--accent) !important;
                box-shadow: 0 0 0 3px var(--accent-light) !important;
                background-color: var(--bg-accent-lighter) !important;
            }
            
            /* ===== CHECKBOXES ===== */
            .stCheckbox > label {
                font-size: var(--text-sm) !important;
                color: var(--text-primary) !important;
                font-weight: 500 !important;
                cursor: pointer !important;
                margin-bottom: 0 !important;
                display: flex !important;
                align-items: center !important;
                gap: 0.5rem !important;
            }
            
            /* ===== SLIDERS - Color Polish ===== */
            .stSlider > div > div {
                padding: var(--spacing-md) 0 !important;
            }
            
            .stSlider label {
                font-size: var(--text-sm) !important;
                font-weight: 600 !important;
                color: var(--text-primary) !important;
                margin-bottom: var(--spacing-sm) !important;
            }
            
            .stSlider [data-testid="stSliderThumb"] {
                background-color: var(--accent) !important;
            }
            
            /* ===== EXPANDERS ===== */
            .streamlit-expanderHeader {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-sm) !important;
                padding: 0.75rem 1rem !important;
                color: var(--text-primary) !important;
                font-weight: 600 !important;
                font-size: var(--text-sm) !important;
                transition: all 0.15s ease !important;
            }
            
            .streamlit-expanderHeader:hover {
                background-color: var(--bg-primary) !important;
                border-color: var(--accent) !important;
            }
            
            .streamlit-expanderHeader p {
                margin: 0 !important;
            }
            
            /* ===== METRICS ===== */
            .stMetric {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                border-radius: var(--radius-md) !important;
                padding: 1rem !important;
            }
            
            .stMetric > div > label {
                font-size: var(--text-xs) !important;
                font-weight: 700 !important;
                text-transform: uppercase !important;
                letter-spacing: 0.05em !important;
                color: var(--text-secondary) !important;
                margin-bottom: var(--spacing-sm) !important;
            }
            
            .stMetric > div > div > div:first-child {
                font-size: var(--text-2xl) !important;
                font-weight: 700 !important;
                color: var(--accent) !important;
                line-height: 1.2 !important;
            }
            
            .stMetric > div > div > div:last-child {
                font-size: var(--text-xs) !important;
                color: var(--text-secondary) !important;
                margin-top: var(--spacing-xs) !important;
            }
            
            /* ===== STATUS MESSAGES ===== */
            .stSuccess {
                background-color: var(--success-light) !important;
                border-left: 3px solid var(--success) !important;
                border-radius: var(--radius-md) !important;
                padding: 0.75rem 1rem !important;
                color: var(--text-primary) !important;
                font-size: var(--text-sm) !important;
            }
            
            .stError {
                background-color: var(--error-light) !important;
                border-left: 3px solid var(--error) !important;
                border-radius: var(--radius-md) !important;
                padding: 0.75rem 1rem !important;
                color: var(--text-primary) !important;
                font-size: var(--text-sm) !important;
            }
            
            .stWarning {
                background-color: var(--warning-light) !important;
                border-left: 3px solid var(--warning) !important;
                border-radius: var(--radius-md) !important;
                padding: 0.75rem 1rem !important;
                color: var(--text-primary) !important;
                font-size: var(--text-sm) !important;
            }
            
            .stInfo {
                background-color: var(--info-light) !important;
                border-left: 3px solid var(--accent) !important;
                border-radius: var(--radius-md) !important;
                padding: 0.75rem 1rem !important;
                color: var(--text-primary) !important;
                font-size: var(--text-sm) !important;
            }
            
            /* ===== CHAT MESSAGES ===== */
            .stChatMessage {
                background-color: transparent !important;
                padding: 0 !important;
                margin-bottom: var(--spacing-lg) !important;
            }
            
            .stChatMessage > div {
                padding: 0 !important;
                background-color: transparent !important;
            }
            
            .stChatMessage p {
                color: var(--text-primary) !important;
                margin: 0 !important;
            }
            
            /* ===== SPINNER ===== */
            .stSpinner {
                text-align: center !important;
                padding: var(--spacing-lg) 0 !important;
            }
            
            .stSpinner > div > div {
                border-color: var(--accent) !important;
            }
            
            /* ===== DIVIDER ===== */
            hr {
                border: none !important;
                border-top: 1px solid var(--border) !important;
                margin: var(--spacing-lg) 0 !important;
            }
            
            /* ===== TABS ===== */
            .stTabs [role="tablist"] {
                border-bottom: 1px solid var(--border) !important;
                gap: var(--spacing-md) !important;
            }
            
            .stTabs [role="tab"] {
                padding: 0.75rem 1rem !important;
                font-weight: 600 !important;
                font-size: var(--text-sm) !important;
                color: var(--text-secondary) !important;
                border-bottom: 2px solid transparent !important;
                margin-bottom: -1px !important;
                background-color: transparent !important;
                transition: all 0.15s ease !important;
                cursor: pointer !important;
            }
            
            .stTabs [role="tab"]:hover:not([aria-selected="true"]) {
                color: var(--text-primary) !important;
            }
            
            .stTabs [role="tab"][aria-selected="true"] {
                color: var(--accent) !important;
                border-bottom-color: var(--accent) !important;
            }
            
            /* ===== FILE UPLOADER ===== */
            .stFileUploader {
                padding: 0 !important;
            }
            
            .stFileUploader > section > div {
                border: 2px dashed var(--border) !important;
                border-radius: var(--radius-lg) !important;
                background-color: var(--bg-surface) !important;
                padding: 2rem !important;
                text-align: center !important;
                transition: all 0.15s ease !important;
            }
            
            .stFileUploader > section > div:hover {
                border-color: var(--accent) !important;
                background-color: var(--accent-light) !important;
            }
            
            /* ===== LABELS & CAPTIONS ===== */
            .stCaption {
                color: var(--text-secondary) !important;
                font-size: var(--text-xs) !important;
            }
            
            label {
                color: var(--text-primary) !important;
                font-size: var(--text-sm) !important;
                font-weight: 500 !important;
            }
            
            /* ===== RESPONSIVE ===== */
            @media (max-width: 768px) {
                .block-container {
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                    max-width: 100% !important;
                }
                
                section[data-testid="stSidebar"] {
                    padding: 1rem !important;
                }
                
                .stButton button {
                    height: 2.125rem !important;
                    font-size: var(--text-xs) !important;
                    padding: 0.5rem 1rem !important;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def main() -> None:
    load_dotenv()
    st.set_page_config(
        page_title="DocuMind AI",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    initialize_state()
    render_styles()
    render_sidebar()
    
    # TOP ACTION AREA: File uploader + Size info
    st.markdown(
        """
        <div style="margin-bottom: 1rem;">
            <div style="font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); margin-bottom: 0.75rem;">
                Upload documents
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    # File uploader
    uploaded_files = st.file_uploader(
        "📤 Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    
    # File size information
    st.markdown(
        """
        <p style="font-size: 0.8125rem; color: var(--text-tertiary); margin: 0.5rem 0 0 0;">
            Maximum file size: 200 MB per file
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown("")
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            if uploaded_file not in st.session_state.get("uploaded_files_cache", []):
                process_uploaded_documents([uploaded_file], st.session_state.retrieval_k)
        st.session_state.uploaded_files_cache = uploaded_files
    
    # Render current workspace
    workspace = st.session_state.current_workspace
    
    if workspace == "Chat":
        workspace_chat(uploaded_files)
    elif workspace == "Documents":
        workspace_documents()
    elif workspace == "Analyze":
        workspace_analyze()
    elif workspace == "Compare":
        workspace_compare()
    elif workspace == "Evaluation":
        workspace_evaluation()


if __name__ == "__main__":
    main()
