# DocuMind AI - Quick Start Guide

## 30-Second Setup

```bash
cd /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main
pip install -r requirements.txt
# Edit .env and add a Groq or OpenAI API key
streamlit run app.py
```

## What It Does

1. **Upload** PDF documents
2. **Ask** questions about them
3. **Get** answers grounded in your documents with sources cited

## How It Works

```
PDF → Extract → Chunk → Embed → Index → Search → LLM → Answer
```

## File Structure

```
app.py                      Main Streamlit application
src/
  ├─ pdf_processor.py       Extract text from PDFs
  ├─ embeddings.py          Generate semantic embeddings
  ├─ vector_store.py        Index and search with FAISS
  ├─ rag_pipeline.py        Orchestrate retrieval + LLM
  └─ utils.py               Helper functions
```

## Key Features

- 📄 Multiple PDF upload
- 🔍 Semantic search across documents
- 🤖 LLM-powered answers
- 📍 Source citations
- 💬 Conversation history
- ⚡ Fast local embeddings
- 🔒 Secure API key handling

## Technology Stack

- **Streamlit**: Web UI
- **PyPDF2**: PDF extraction
- **HuggingFace**: Embeddings (local)
- **FAISS**: Vector search
- **Groq/OpenAI**: LLM backend
- **LangChain**: RAG orchestration

## Configuration

Edit `.env`:

```
GROQ_API_KEY=your_groq_api_key
# OR
OPENAI_API_KEY=your_openai_api_key
```

## Run Tests

```bash
python3 test_rag_pipeline.py
```

All tests should pass ✅

## Troubleshooting

**App won't start?**
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check .env file exists

**No answers generated?**
- Ensure API key is valid
- Check internet connection
- Verify PDF contains extractable text

**Slow processing?**
- First-time embeddings model download takes a minute
- Subsequent runs are faster

## Interview Explanation

*"DocuMind AI combines document retrieval with language models. When you upload PDFs, the system extracts and chunks the text, creates semantic embeddings using HuggingFace, and stores them in FAISS. When you ask a question, it finds the most relevant chunks through semantic similarity search, sends them with your question to Groq LLM, and generates an answer. The LLM is instructed to use only the provided context, preventing hallucination."*

## Next Steps

1. ✅ Setup dependencies
2. ✅ Get API key (Groq or OpenAI)
3. ✅ Run the app
4. ✅ Upload a PDF
5. ✅ Ask a question
6. ✅ Review the answer and sources

---

**Status**: ✅ **Ready to Use**

For detailed information, see README.md and IMPLEMENTATION_REPORT.md
