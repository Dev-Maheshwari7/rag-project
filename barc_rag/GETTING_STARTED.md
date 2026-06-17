# 🚀 BARC RAG - Getting Started (Copy-Paste Commands)

## Step 1: Navigate to Project

```bash
cd c:\Users\Rinku\OneDrive\Desktop\ragsys\barc_rag
```

## Step 2: Install Python Packages

```bash
pip install -r requirements.txt
```

*Expected: ~2-3 minutes. Models download on first use.*

## Step 3: Start Docker Services

```bash
docker-compose up -d
```

*Expected: Docker pulls images and starts containers.*

## Step 4: Wait for Services

```bash
# Windows PowerShell
Start-Sleep -Seconds 15

# Or manually wait 15 seconds
```

## Step 5: Verify Services

```bash
# Check containers are running
docker ps

# Expected output: 2 containers (qdrant, barc_postgres)
```

## Step 6: Add xAI API Key

**Edit .env file:**

Find this line:
```env
XAI_API_KEY=your_xai_api_key_here
```

Replace with your actual key:
```env
XAI_API_KEY=xai-xxx...xxx
```

Save file (Ctrl+S in VS Code).

## Step 7: Add Test Documents (Optional)

Place any PDFs or DOCX files in:
```
c:\Users\Rinku\OneDrive\Desktop\ragsys\barc_rag\documents\
```

## Step 8: Launch the Application

```bash
streamlit run app/main.py
```

*Expected: Browser opens at http://localhost:8501/*

## Step 9: Index Documents

In the Streamlit sidebar:
1. Click **🔄 Start Ingestion**
2. Wait for completion (~5-30 minutes depending on document count)

## Step 10: Start Querying!

1. Type a question in the query box
2. Click **Search & Generate Answer**
3. Review the answer and sources

---

## 🐛 Troubleshooting Quick Fixes

### "Docker not found"
```bash
# Install Docker Desktop from https://docker.com
# Then restart terminal
```

### "PostgreSQL connection refused"
```bash
# Wait 15 seconds, then restart
docker-compose restart postgres
```

### "xAI API key invalid"
```bash
# Check .env file - ensure:
# - Correct API key
# - No extra spaces or newlines
# - File is saved
```

### "Models still downloading"
```bash
# First run is slow while downloading:
# - all-MiniLM-L6-v2 (~50MB)
# - cross-encoder (~50MB)
# This happens in background, be patient
```

### "Port 6333 already in use"
```bash
# Qdrant port is busy, stop other services:
docker-compose down
docker-compose up -d
```

---

## 📚 Documentation Files

```
README.md          ← Complete usage guide (START HERE)
QUICKSTART.md      ← 5-minute quick start
ARCHITECTURE.md    ← Technical deep dive
TESTING.md         ← Validation procedures
SYSTEM_OVERVIEW.md ← What was built
PROJECT_SUMMARY.md ← Implementation details
```

---

## ✅ Success Indicators

After following all steps, you should see:

- ✅ `docker ps` shows 2 containers running
- ✅ Streamlit UI opens in browser
- ✅ Sidebar shows "Total Documents" count
- ✅ Ingestion completes without errors
- ✅ Sample query returns an answer
- ✅ Sources are displayed with citations

---

## 🎯 Sample Query Test

Try these questions (after indexing):

**If you have product docs:**
- "What products do you offer?"
- "How much does product X cost?"
- "What are the features of X?"

**If you have reports:**
- "What are the key findings?"
- "Summarize the executive summary"
- "What data is in Table 5?"

**General:**
- "What topics are covered?"
- "Who is mentioned most?"
- "What are the main conclusions?"

---

## 🛑 Stopping Services

```bash
# Stop all services (keeps data)
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Stop, remove, and delete all data
docker-compose down -v
rm -r qdrant_storage pg_data ingest_log.db
```

---

## 📞 Need Help?

1. Check the relevant documentation (see above)
2. Review Streamlit console output (terminal running the app)
3. Check Docker logs:
   ```bash
   docker-compose logs postgres
   docker-compose logs qdrant
   ```
4. Ensure all `.env` variables are set
5. Verify Docker containers are healthy: `docker ps`

---

## 🚀 Next: Advanced Usage

Once running, explore:

**Custom Queries:**
- Try complex multi-part questions
- Test with different document types
- See how sources are ranked

**Configuration:**
- Edit `config.py` to adjust parameters
- Change chunk size, batch size, top-k values
- Customize prompts in `llm/grok_client.py`

**Integration:**
- Build REST API on top
- Add to existing applications
- Stream responses
- Implement conversation memory

---

**Ready? Start with: `cd barc_rag && setup.bat` (Windows) or `./setup.sh` (Mac/Linux)**

Questions? Read [README.md](README.md) for comprehensive guide.

Enjoy your RAG system! 🎉
