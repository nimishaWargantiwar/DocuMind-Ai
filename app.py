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
    """Main chat workspace."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Chat", doc_count)
    
    if st.session_state.vector_store is None:
        # Empty state
        st.markdown(
            """
            <div style="text-align: center; padding: 3rem 2rem; margin: 2rem 0;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📚</div>
                <h2 style="font-size: 1.875rem; font-weight: 700; color: #111827; margin: 0 0 0.5rem 0;">
                    Understand your documents
                </h2>
                <p style="font-size: 1rem; color: #667085; max-width: 500px; margin: 0 auto;">
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
            st.info("📤 Use the file uploader in the sidebar to get started")
    
    else:
        # Chat ready
        st.markdown(
            f"""
            <div style="padding: 0.75rem 1rem; background: #F3F4F6; border-radius: 0.5rem; margin-bottom: 1.5rem; font-size: 0.875rem; color: #667085;">
                <span style="font-weight: 500;">✅ Ready</span> · {st.session_state.indexed_chunk_count} chunks indexed
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Chat history
        render_chat_history()
        
        # Chat input
        st.markdown("")
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
    """Documents library workspace."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Documents", doc_count)
    
    if doc_count == 0:
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem; color: #667085;">
                <p>No documents uploaded yet.</p>
                <p style="font-size: 0.875rem;">Use the uploader in the sidebar.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("**Your documents**")
        
        for doc in doc_manager.get_all_documents():
            col1, col2 = st.columns([1, 0.15], gap="large")
            
            with col1:
                st.markdown(
                    f"""
                    <div style="padding: 1rem; border: 1px solid #E5E7EB; border-radius: 0.5rem; background: #FFFFFF;">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <div>
                                <p style="margin: 0; font-weight: 600; color: #111827; font-size: 0.9375rem;">
                                    📄 {doc.filename}
                                </p>
                                <p style="margin: 0.25rem 0 0 0; font-size: 0.8125rem; color: #667085;">
                                    {doc.page_count} pages · {doc.total_chunks} chunks
                                </p>
                            </div>
                            <span style="font-size: 0.75rem; font-weight: 600; color: #22C55E; background: #ECFDF5; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">
                                ✓ Ready
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            with col2:
                if st.button("🗑️", key=f"del_doc_{doc.doc_id}", help="Delete"):
                    doc_manager.remove_document(doc.doc_id)
                    st.rerun()


# ============================================================
# WORKSPACE: ANALYZE
# ============================================================

def workspace_analyze() -> None:
    """Document analysis workspace."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Analyze", doc_count)
    
    if doc_count == 0:
        st.info("Upload documents first to analyze them.")
        return
    
    if doc_manager.count_selected() == 0:
        st.info("Select documents in the sidebar to analyze them.")
        return
    
    st.markdown("**Document analysis**")
    
    selected_docs = doc_manager.get_selected_documents()
    doc_names = ", ".join([d.filename[:20] for d in selected_docs])
    st.caption(f"📄 {doc_names}")
    
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
    """Document comparison workspace."""
    doc_manager = st.session_state.document_manager
    doc_count = doc_manager.count_documents()
    
    render_app_header("Compare", doc_count)
    
    if doc_count < 2:
        st.info("Upload at least 2 documents to compare them.")
        return
    
    st.markdown("**Compare documents**")
    
    docs = doc_manager.get_all_documents()
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        doc_a = st.selectbox(
            "Document A",
            [d.filename for d in docs],
            key="doc_a",
            label_visibility="collapsed",
        )
    
    with col2:
        doc_b = st.selectbox(
            "Document B",
            [d.filename for d in docs if d.filename != doc_a],
            key="doc_b",
            label_visibility="collapsed",
        )
    
    if st.button("Compare documents", use_container_width=True):
        st.info("Document comparison coming soon")


# ============================================================
# WORKSPACE: EVALUATION
# ============================================================

def workspace_evaluation() -> None:
    """RAG evaluation workspace."""
    render_app_header("Evaluation")
    
    if "evaluator" not in st.session_state:
        from src.evaluator import RAGEvaluator
        st.session_state.evaluator = RAGEvaluator()
    
    evaluator = st.session_state.evaluator
    
    if not evaluator.results:
        st.info("Evaluation metrics will appear after asking questions.")
        return
    
    st.markdown("**Quality metrics**")
    
    metrics = evaluator.compute_metrics()
    
    col1, col2, col3, col4 = st.columns(4, gap="large")
    
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
    
    if st.button("Reset metrics", use_container_width=False):
        evaluator.reset()
        st.rerun()


# ============================================================
# NAVIGATION
# ============================================================

def render_sidebar() -> None:
    """Render navigation sidebar."""
    with st.sidebar:
        st.markdown(
            """
            <div style="margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 1px solid #E5E7EB;">
                <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #667085; margin-bottom: 1rem;">
                    Workspace
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        workspaces = [
            ("💬", "Chat"),
            ("📚", "Documents"),
            ("🧠", "Analyze"),
            ("🔀", "Compare"),
            ("📊", "Evaluation"),
        ]
        
        for icon, name in workspaces:
            if st.button(
                f"{icon} {name}",
                key=f"ws_{name}",
                use_container_width=True,
                help=f"Go to {name}",
            ):
                st.session_state.current_workspace = name
                st.rerun()
        
        st.markdown("---")
        
        # File uploader
        st.markdown(
            """
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #667085; margin-bottom: 0.75rem;">
                Upload
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Document list with selection
        doc_manager = st.session_state.document_manager
        if doc_manager.count_documents() > 0:
            st.markdown(
                f"<p style='font-size: 0.875rem; color: #667085;'>{doc_manager.count_documents()} uploaded</p>",
                unsafe_allow_html=True,
            )
            
            for doc in doc_manager.get_all_documents():
                is_selected = st.checkbox(
                    doc.filename,
                    value=doc.doc_id in doc_manager.selected_doc_ids,
                    key=f"sel_{doc.doc_id}",
                )
                if is_selected:
                    doc_manager.select_document(doc.doc_id)
                else:
                    doc_manager.deselect_document(doc.doc_id)
        
        st.markdown("---")
        
        # Settings
        st.markdown(
            """
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #667085; margin-bottom: 0.75rem;">
                Settings
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        with st.expander("⚙️ Advanced"):
            st.session_state.api_key = st.text_input(
                "API Key",
                type="password",
                value=st.session_state.api_key,
                help="Leave blank to use GROQ_API_KEY",
            )
            
            st.session_state.retrieval_k = st.slider(
                "Retrieved chunks",
                min_value=2,
                max_value=8,
                value=st.session_state.retrieval_k,
            )
            
            st.session_state.use_hybrid = st.checkbox(
                "Hybrid retrieval",
                value=st.session_state.use_hybrid,
            )
            
            st.session_state.temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.temperature,
                step=0.05,
            )
        
        st.markdown("---")
        
        # Status
        groq_ok = bool(os.getenv("GROQ_API_KEY"))
        openai_ok = bool(st.session_state.api_key.strip() or os.getenv("OPENAI_API_KEY"))
        
        if groq_ok or openai_ok:
            st.success("✅ LLM ready")
        else:
            st.warning("⚠️ Configure API key")


def render_app_header(workspace: str, document_count: int = 0) -> None:
    """Render workspace header."""
    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem 0; border-bottom: 1px solid #E5E7EB; margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="font-size: 1rem; font-weight: 700; color: #667085; text-transform: uppercase; letter-spacing: 0.05em;">
                    {workspace}
                </span>
            </div>
            {f'<div style="color: #667085; font-size: 0.875rem;">{document_count} documents</div>' if document_count > 0 else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_styles() -> None:
    """Render minimal, professional styles."""
    st.markdown(
        """
        <style>
            /* ===== COLOR PALETTE (LIGHT, MINIMAL, EDITORIAL) ===== */
            :root {
                --bg-primary: #F7F8FA;
                --bg-surface: #FFFFFF;
                --text-primary: #111827;
                --text-secondary: #667085;
                --accent: #4F46E5;
                --border: #E5E7EB;
                --success: #22C55E;
                --warning: #F59E0B;
                --error: #EF4444;
            }
            
            /* ===== GLOBAL STYLES ===== */
            body {
                background-color: var(--bg-primary);
                color: var(--text-primary);
            }
            
            .main {
                background-color: var(--bg-primary);
            }
            
            .block-container {
                max-width: 900px;
                padding-top: 2rem !important;
                padding-bottom: 2rem !important;
            }
            
            /* ===== MARKDOWN ===== */
            .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
                color: var(--text-primary) !important;
                font-weight: 700 !important;
            }
            
            .stMarkdown p {
                color: var(--text-primary) !important;
                line-height: 1.6 !important;
            }
            
            /* ===== SIDEBAR ===== */
            section[data-testid="stSidebar"] {
                background-color: var(--bg-surface) !important;
                border-right: 1px solid var(--border) !important;
            }
            
            section[data-testid="stSidebar"] * {
                color: var(--text-primary) !important;
            }
            
            /* ===== BUTTONS ===== */
            .stButton button {
                background-color: var(--accent) !important;
                color: white !important;
                border: none !important;
                font-weight: 600 !important;
                border-radius: 0.375rem !important;
            }
            
            .stButton button:hover {
                background-color: #4338CA !important;
            }
            
            /* ===== INPUTS ===== */
            .stTextInput input,
            .stTextArea textarea,
            .stChatInput input,
            .stSelectbox select {
                background-color: var(--bg-surface) !important;
                color: var(--text-primary) !important;
                border: 1px solid var(--border) !important;
                border-radius: 0.375rem !important;
            }
            
            /* ===== CHAT ===== */
            .stChatMessage {
                background-color: transparent !important;
            }
            
            /* ===== EXPANDERS ===== */
            .streamlit-expanderHeader {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                color: var(--text-primary) !important;
            }
            
            /* ===== METRICS ===== */
            .stMetric {
                background-color: var(--bg-surface) !important;
                border: 1px solid var(--border) !important;
                border-radius: 0.375rem !important;
                padding: 1rem !important;
            }
            
            /* ===== STATUS MESSAGES ===== */
            .stSuccess {
                background-color: #ECFDF5 !important;
                border-left: 3px solid var(--success) !important;
                color: var(--text-primary) !important;
            }
            
            .stError {
                background-color: #FEF2F2 !important;
                border-left: 3px solid var(--error) !important;
                color: var(--text-primary) !important;
            }
            
            .stWarning {
                background-color: #FFFBEB !important;
                border-left: 3px solid var(--warning) !important;
                color: var(--text-primary) !important;
            }
            
            .stInfo {
                background-color: #EEF2FF !important;
                border-left: 3px solid var(--accent) !important;
                color: var(--text-primary) !important;
            }
            
            /* ===== CHECKBOXES & LABELS ===== */
            .stCheckbox label, .stSelectbox label, .stRadio label {
                color: var(--text-primary) !important;
            }
            
            /* ===== SPINNER ===== */
            .stSpinner div {
                border-color: var(--accent) !important;
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
    
    # File uploader in top area
    uploaded_files = st.file_uploader(
        "📤 Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    
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
