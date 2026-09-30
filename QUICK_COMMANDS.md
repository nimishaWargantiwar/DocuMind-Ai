# DocuMind AI - Quick Command Reference

## Getting Started (First Time Setup)

```bash
# Navigate to project directory
cd ~/Desktop/DESKTOP/PROJECTS/ChatPDF-main

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Verify .env file exists with Groq API key
cat .env
```

## Running the Application

```bash
# Start the Streamlit app
streamlit run app.py
```

The app will automatically open at `http://localhost:8501`

## Testing the RAG Pipeline

```bash
# Run comprehensive pipeline test
python << 'ENDTEST'
import os
from dotenv import load_dotenv
load_dotenv(".env")

from src.embeddings import load_embeddings
from src.vector_store import build_vector_store
from src.rag_pipeline import build_pipeline
from langchain_core.documents import Document

# Create test documents
test_docs = [
    Document(
        page_content="Apple was founded by Steve Jobs in 1976.",
        metadata={"source": "tech.pdf", "page": 1, "chunk_index": 1}
    ),
]

embeddings = load_embeddings()
vector_store = build_vector_store(test_docs, embeddings)
pipeline = build_pipeline(vector_store, retrieval_k=1, api_key=None, temperature=0.2)

result = pipeline.ask("Who founded Apple?", [])
print(f"✅ Answer: {result.answer}")
ENDTEST
```

## Verifying Groq API Connection

```bash
# Check API key is loaded
python << 'ENDCHECK'
import os
from dotenv import load_dotenv
load_dotenv(".env")

key = os.getenv("GROQ_API_KEY")
if key:
    print(f"✅ API Key loaded (length: {len(key)})")
else:
    print("❌ API Key NOT found in .env")
ENDCHECK
```

## Troubleshooting

### Check Python Version
```bash
python --version  # Should be 3.10+
```

### Reinstall Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Clear Cache and Restart
```bash
# Deactivate and reactivate venv
deactivate
source .venv/bin/activate

# Restart streamlit
streamlit run app.py
```

### Check Groq Models
```bash
python << 'ENDMODELS'
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(".env")
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
models = client.models.list()
print("Available models:")
for m in models.data:
    print(f"  - {m.id}")
ENDMODELS
```

## Key Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit web interface |
| `src/rag_pipeline.py` | RAG pipeline & LLM integration |
| `src/pdf_processor.py` | PDF text extraction |
| `src/embeddings.py` | Embedding model loading |
| `src/vector_store.py` | FAISS vector store |
| `.env` | API keys and configuration |
| `requirements.txt` | Python dependencies |

## Useful Tips

### Enable Debug Mode
```bash
streamlit run app.py --logger.level=debug
```

### Run on Specific Port
```bash
streamlit run app.py --server.port 8502
```

### Run from Different Directory
```bash
streamlit run /path/to/app.py
```

### View Streamlit Logs
```bash
# Logs appear in the terminal where you ran streamlit
# Look for [timestamp] messages
```

## Performance Tips

1. **First Run**: Embedding model downloads (~400MB). Be patient.
2. **Large PDFs**: Chunking and embedding large documents takes time. Progress shows in UI.
3. **Rate Limits**: Groq API has rate limits. Space out requests for best performance.
4. **GPU Memory**: Uses CPU. For 100K+ chunks, consider GPU acceleration.

## Support

- **App won't start**: Check Python version and reinstall dependencies
- **API errors**: Verify GROQ_API_KEY in .env is correct
- **Slow responses**: First run of embedding model is slow (cached after)
- **PDF extraction fails**: Ensure PDF is text-based, not image-only

---

**Last Updated**: September 30, 2026  
**Status**: ✅ Production Ready
