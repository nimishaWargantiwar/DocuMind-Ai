from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

from langchain_classic.chains.history_aware_retriever import create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    source_documents: list[Document]


def _load_chat_model(api_key: str | None, temperature: float):
    """Load LLM: prefer Groq, fall back to OpenAI if configured."""
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = api_key or os.getenv("OPENAI_API_KEY")

    if groq_key:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
            temperature=temperature,
            api_key=groq_key,
        )

    if openai_key:
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            api_key=openai_key,
        )

    raise ValueError(
        "No LLM API key configured. Set GROQ_API_KEY or OPENAI_API_KEY in your .env file."
    )


def _build_history_aware_prompt() -> ChatPromptTemplate:
    """Prompt for reformulating follow-up questions into standalone questions."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Given a chat history and a follow-up question, rephrase the follow-up question "
                "to be a standalone question that includes all necessary context. "
                "Do not answer the question, only reformulate it.",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )


def _build_answer_prompt() -> tuple[ChatPromptTemplate, PromptTemplate]:
    """Prompt for generating answers based on retrieved context."""
    document_prompt = PromptTemplate.from_template(
        "Source: {source}\nPage: {page}\nChunk: {chunk_index}\n\n{page_content}"
    )

    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are DocuMind AI, a document question-answering assistant. "
                "Answer the user's question using ONLY the provided document context. "
                "If the answer cannot be found in the provided context, clearly state that "
                "the information is not available in the uploaded documents. "
                "Do not invent facts or use knowledge outside the provided context. "
                "Keep responses concise, accurate, and grounded in the retrieved text.",
            ),
            MessagesPlaceholder("chat_history"),
            (
                "human",
                "Question: {input}\n\nContext from documents:\n{context}",
            ),
        ]
    )

    return answer_prompt, document_prompt


def _to_langchain_messages(chat_history: Sequence[BaseMessage | dict]) -> list[BaseMessage]:
    """Convert mixed message types to LangChain BaseMessage format."""
    messages: list[BaseMessage] = []

    for message in chat_history:
        if isinstance(message, BaseMessage):
            messages.append(message)
            continue

        role = message.get("role")
        content = message.get("content", "")

        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    return messages


@dataclass
class DocuMindPipeline:
    """Complete RAG pipeline for document question-answering."""

    retriever: object
    history_aware_retriever: object
    answer_chain: object

    def ask(self, question: str, chat_history: Sequence[BaseMessage | dict]) -> AnswerResult:
        """Generate an answer to a question using retrieved document context."""
        messages = _to_langchain_messages(chat_history)

        # Retrieve relevant chunks directly using the question
        # (history-aware retriever returns documents, not reformulated question)
        retrieved_documents = self.history_aware_retriever.invoke(
            {"input": question, "chat_history": messages}
        )

        # Generate answer using context
        answer = self.answer_chain.invoke(
            {
                "input": question,
                "chat_history": messages,
                "context": retrieved_documents,
            }
        )

        # Handle both dict and string responses from LLM
        if isinstance(answer, dict):
            answer_text = str(answer.get("text", answer.get("answer", "")))
        else:
            answer_text = str(answer)

        return AnswerResult(answer=answer_text, source_documents=list(retrieved_documents))


def build_pipeline(
    vector_store, *, retrieval_k: int, api_key: str | None, temperature: float, use_hybrid_retrieval: bool = False
) -> DocuMindPipeline:
    """Construct the complete RAG pipeline."""
    llm = _load_chat_model(api_key=api_key, temperature=temperature)
    
    # Use hybrid retrieval if requested
    if use_hybrid_retrieval:
        try:
            from .retriever import HybridRetriever
            # Get documents from vector store (attempt to retrieve all for BM25 indexing)
            all_docs = []
            try:
                # Try to get docstore if available
                if hasattr(vector_store, 'docstore'):
                    all_docs = list(vector_store.docstore._dict.values())
            except:
                pass
            
            if all_docs:
                hybrid_retriever = HybridRetriever(vector_store, all_docs)
                retriever = hybrid_retriever.retrieve
                # Wrap in a class-like object for compatibility
                class WrappedHybridRetriever:
                    def __init__(self, fn, k):
                        self.fn = fn
                        self.k = k
                    
                    def invoke(self, query: str):
                        return self.fn(query, k=self.k)
                
                retriever = WrappedHybridRetriever(retriever, retrieval_k)
            else:
                # Fallback to standard retrieval
                retriever = vector_store.as_retriever(search_kwargs={"k": retrieval_k})
        except Exception:
            # Fallback to standard retrieval if hybrid setup fails
            retriever = vector_store.as_retriever(search_kwargs={"k": retrieval_k})
    else:
        retriever = vector_store.as_retriever(search_kwargs={"k": retrieval_k})

    # Create history-aware retriever that reformulates questions
    history_prompt = _build_history_aware_prompt()
    history_aware_retriever = create_history_aware_retriever(llm, retriever, history_prompt)

    # Create answer generation chain
    answer_prompt, document_prompt = _build_answer_prompt()
    answer_chain = create_stuff_documents_chain(llm, answer_prompt, document_prompt=document_prompt)

    return DocuMindPipeline(
        retriever=retriever,
        history_aware_retriever=history_aware_retriever,
        answer_chain=answer_chain,
    )
