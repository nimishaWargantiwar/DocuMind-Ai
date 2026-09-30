# DocuMind AI - Quick Command Reference

## Running the Application

### Start the App
```bash
cd /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main
source .venv/bin/activate
streamlit run app.py
```

**Then open**: `http://localhost:8501`

---

## Testing

### Run Unit Tests (No API calls)
```bash
python test_rag_pipeline.py
```

### Run Implementation Tests
```bash
python test_implementation.py
```

### Run End-to-End Tests (Requires GROQ_API_KEY)
```bash
python test_e2e_rag.py
```

### Run All Tests
```bash
python test_rag_pipeline.py && \
python test_implementation.py && \
python test_e2e_rag.py
```

---

## Environment Setup

### Check Configuration
```bash
cat .env | grep GROQ_API_KEY
```

### Update API Key
```bash
# Edit .env and add your key:
GROQ_API_KEY=your_key_here
```

### Verify Dependencies
```bash
pip list | grep -E "streamlit|langchain|faiss|groq"
```

### Reinstall Dependencies
```bash
pip install -r requirements.txt --upgrade
```

---

## Python Scripts

### Check if Core RAG Works
```bash
python -c "from src.embeddings import load_embeddings; load_embeddings(); print('✅ Embeddings OK')"
```

### Quick API Test
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
from groq import Groq
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
response = client.chat.completions.create(
    model='qwen/qwen3.8-27b',
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=10
)
print('✅ Groq API OK:', response.choices[0].message.content)
"
```

### Syntax Check (All Python Files)
```bash
python -m py_compile app.py src/*.py
echo "✅ All files compile successfully"
```

---

## File Structure

### View Project Tree
```bash
tree -L 2 -I '__pycache__|.venv' /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main
```

### Key Files
```bash
# Main application
cat app.py | head -50

# Core RAG pipeline
cat src/rag_pipeline.py | head -50

# Document manager
cat src/document_manager.py | head -30

# Tests
ls -lah test_*.py
```

---

## Git Operations

### Check Status
```bash
git status
```

### Check .gitignore (Verify .env protected)
```bash
grep ".env" .gitignore
```

### View Changes
```bash
git diff app.py
git diff src/
```

---

## Documentation

### View README
```bash
cat README.md | head -100
```

### View Implementation Report
```bash
cat IMPLEMENTATION_COMPLETE.md | head -50
```

### View Project Status
```bash
cat PROJECT_STATUS_REPORT.md | head -100
```

---

## Troubleshooting

### Check Python Version
```bash
python --version  # Should be 3.10+
```

### Check Virtual Environment
```bash
which python  # Should show .venv path
```

### Clear Cache and Restart
```bash
# Windows
rmdir /s __pycache__ src/__pycache__

# Mac/Linux
find . -type d -name __pycache__ -exec rm -r {} +

# Restart app
streamlit run app.py
```

### Check System Resources
```bash
# Show available memory
free -h  # Linux
vm_stat  # Mac

# Kill any hanging processes
pkill -f streamlit
```

### View Logs
```bash
# Logs appear in the terminal where you ran streamlit
# Look for timestamps and error messages
```

---

## Advanced Usage

### Run Streamlit on Specific Port
```bash
streamlit run app.py --server.port 8502
```

### Run with Debug Mode
```bash
streamlit run app.py --logger.level=debug
```

### Run from Different Directory
```bash
streamlit run /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main/app.py
```

### Generate Streamlit Config
```bash
streamlit config show
```

---

## File Management

### Backup Project
```bash
cp -r ChatPDF-main ChatPDF-main-backup-$(date +%Y%m%d)
```

### List All Python Files
```bash
find . -name "*.py" -type f
```

### Count Lines of Code
```bash
find src -name "*.py" -type f -exec wc -l {} + | tail -1
```

### Check File Sizes
```bash
du -sh src/* app.py
```

---

## Development

### Format Code (Optional)
```bash
# Install black
pip install black

# Format all files
black app.py src/
```

### Check Code Quality (Optional)
```bash
# Install flake8
pip install flake8

# Check
flake8 app.py src/
```

### Run Type Checking (Optional)
```bash
# Install mypy
pip install mypy

# Check types
mypy app.py --ignore-missing-imports
```

---

## Performance Profiling

### Profile App Startup
```bash
time streamlit run app.py --logger.level=error
```

### Profile Functions
```python
# Add to app.py temporarily:
import time

def timed_function(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.3f}s")
        return result
    return wrapper

@timed_function
def process_uploaded_documents(files, k):
    # ... implementation
```

---

## Deployment

### Create Production Archive
```bash
zip -r ChatPDF-main-prod.zip . \
  -x "*.pyc" "__pycache__/*" ".venv/*" ".git/*" "*.md"
```

### Deploy to Streamlit Cloud
```bash
streamlit deploy
```

### Environment Variables for Production
```bash
# Set in cloud platform:
GROQ_API_KEY=your_production_key
```

---

## Quick Checks

### Verify All Components
```bash
python -c "
print('Checking components...')
from src.embeddings import load_embeddings
from src.pdf_processor import extract_pdf_documents
from src.rag_pipeline import build_pipeline
from src.document_manager import DocumentManager
from src.retriever import HybridRetriever
from src.evaluator import RAGEvaluator
print('✅ All components import successfully')
"
```

### Test Complete Pipeline
```bash
python test_e2e_rag.py
```

### Verify Security
```bash
# Check for hardcoded secrets
grep -r "gsk_" src/ app.py || echo "✅ No hardcoded API keys"
grep -r "sk_" src/ app.py || echo "✅ No OpenAI keys"
```

---

## Usage Examples

### Run Simple Q&A Test
```python
# Save as test_qa.py
import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from src.embeddings import load_embeddings
from src.vector_store import chunk_documents, build_vector_store
from src.rag_pipeline import build_pipeline

load_dotenv()

docs = [
    Document(
        page_content="Python is a programming language",
        metadata={"source": "test.pdf", "page": 1, "chunk_index": 1}
    )
]

embeddings = load_embeddings()
chunks = chunk_documents(docs)
vs = build_vector_store(chunks.chunks, embeddings)
pipeline = build_pipeline(vs, retrieval_k=1, api_key=None, temperature=0.2)
result = pipeline.ask("What is Python?", [])
print(result.answer)
```

Then run:
```bash
python test_qa.py
```

---

## Monitoring

### Check Memory Usage (While App Running)
```bash
# Linux
ps aux | grep streamlit | grep -v grep

# Mac
ps aux | grep streamlit | head -5
```

### Monitor Groq API Calls
```bash
# Visit Groq console to see usage
# https://console.groq.com/usage
```

---

## Help & Documentation

### View Available Commands
```bash
streamlit --help
```

### Streamlit Documentation
```bash
# Open in browser:
# https://docs.streamlit.io
```

### LangChain Documentation
```bash
# https://python.langchain.com
```

---

## One-Liners

### Quick App Start
```bash
cd /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main && source .venv/bin/activate && streamlit run app.py
```

### Quick Test
```bash
cd /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main && python test_e2e_rag.py 2>&1 | tail -20
```

### Quick Syntax Check
```bash
cd /Users/nimisha/Desktop/DESKTOP/PROJECTS/ChatPDF-main && python -m py_compile app.py src/*.py && echo "✅ OK"
```

### Quick Groq Test
```bash
python -c "import os; os.getenv('GROQ_API_KEY') and print('✅ Key set') or print('❌ Key missing')"
```

---

**Last Updated**: September 30, 2026  
**Status**: Ready to Use ✅
