# How to Run DocuMind AI

## Prerequisites Check ✅

Before running, verify you have:
- ✅ Python 3.10+ installed
- ✅ Virtual environment created (.venv)
- ✅ Dependencies installed
- ✅ .env file with GROQ_API_KEY

## Step 1: Open Terminal

Navigate to the project directory:
```bash
cd ~/Desktop/DESKTOP/PROJECTS/ChatPDF-main
```

## Step 2: Activate Virtual Environment

```bash
source .venv/bin/activate
```

You should see `(.venv)` at the start of your terminal prompt.

## Step 3: Start the Application

```bash
streamlit run app.py
```

## What to Expect

### Terminal Output:
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501

  For better performance, install pyarrow: `pip install --upgrade pyarrow`
```

### Browser Opens Automatically
The app opens at `http://localhost:8501` showing the DocuMind AI interface.

## Using the Application

### 1. Upload PDF Documents
- Click "Upload one or more PDF documents"
- Select PDF files from your computer
- Supports multiple files simultaneously

### 2. Process Documents
- Click the blue "Process Documents" button
- Wait for the status message (usually 5-10 seconds for small PDFs)
- You'll see "Processed X document(s) into Y searchable chunk(s)"

### 3. Ask Questions
- Type a question in the chat input box
- Questions are answered based on the uploaded PDF content
- Sources are shown with filename and page number

### 4. Adjust Settings (Optional)
In the sidebar:
- **OpenAI API Key**: Leave blank (uses Groq by default)
- **Number of retrieved chunks**: Default 4 (change if needed)
- **Temperature**: Default 0.2 (lower = more faithful to source)

### 5. Clear or Reset
- **Clear Conversation**: Removes chat history, keeps documents indexed
- **Reset Documents**: Removes everything, start fresh

## Example Workflow

1. Upload: `financial_report.pdf`
2. Wait for: "Processed 1 document(s) into 15 searchable chunk(s)"
3. Ask: "What was the company's revenue?"
4. Get: "The company's revenue was $50M." (with source: financial_report.pdf, Page 2)

## Stopping the Application

### In Terminal
Press `Ctrl+C` to stop the Streamlit server.

### Browser
Simply close the browser tab.

## Common Issues

### App doesn't start
```bash
# Check Python version
python --version

# Reinstall dependencies
pip install -r requirements.txt

# Try again
streamlit run app.py
```

### Error: "GROQ_API_KEY not configured"
- Open `.env` file
- Verify `GROQ_API_KEY=your_groq_api_key_here
- Save the file
- Restart the app (Ctrl+C and run again)

### Slow First Run
- First run downloads embedding model (~400MB)
- This is cached for subsequent runs
- Be patient, it takes 1-2 minutes first time

### PDF Upload Fails
- Ensure PDF is text-based (not scanned image)
- Try a different PDF to verify
- Check terminal for error details

## Performance

| Action | Time |
|--------|------|
| App startup | ~5 seconds |
| Document processing (1 PDF) | ~2-5 seconds |
| First embedding load | ~1-2 minutes |
| Subsequent runs | ~3-5 seconds |
| Question answering | ~2-3 seconds |

## Tips for Best Results

✅ **Use text-based PDFs** (searchable text, not scanned images)
✅ **Ask specific questions** about the document content
✅ **Use multiple PDFs** to build richer knowledge base
✅ **Adjust temperature** lower (0.1-0.3) for factual answers
✅ **Clear history** periodically to maintain context window

## Next Steps

### Learn More
- Read `PROJECT_STATUS_REPORT.md` for detailed verification
- Check `QUICK_COMMANDS.md` for testing and troubleshooting
- Review `LLM_INTEGRATION_REPORT.md` for technical details

### Deploy (Optional)
Once you're confident with local testing:
- Deploy to Streamlit Cloud: `streamlit deploy`
- Deploy to cloud service: AWS, Google Cloud, Azure
- Self-host: Run on VPS/server

## Support

If something isn't working:
1. Check the error message in the Streamlit UI (red box)
2. Check terminal output for detailed error logs
3. Restart the app (Ctrl+C, then `streamlit run app.py`)
4. Verify all files exist: `ls -la`

---

**The app is production-ready. Enjoy DocuMind AI! 🚀**
