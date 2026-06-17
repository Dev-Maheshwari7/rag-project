# BARC RAG System - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Docker & Docker Compose installed
- Python 3.9+
- xAI API key (get one at https://console.x.ai/)

### Step 1: Initial Setup (2 min)

**Windows:**
```bash
setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
pip install -r requirements.txt
docker-compose up -d
```

### Step 2: Configure API Key (30 sec)

Edit `.env`:
```env
XAI_API_KEY=your_actual_key_here
```

### Step 3: Add Documents (1 min)

Place PDF/DOCX files in `documents/`:
```
documents/
├── report1.pdf
├── manual.docx
└── guide.pdf
```

### Step 4: Launch UI (30 sec)

```bash
streamlit run app/main.py
```

Open browser to `http://localhost:8501/`

### Step 5: Index Documents (varies)

Click **🔄 Start Ingestion** in the sidebar and wait for completion.

### Step 6: Query!

Ask questions in the query box:
- "What is the main topic?"
- "Summarize the findings"
- "What data is in the tables?"

---

## 🔧 What Each Component Does

| Component | Purpose | Tech |
|-----------|---------|------|
| **Parser** | Extracts text & tables from PDFs/DOCX | Unstructured + hi_res |
| **Chunker** | Splits text (512 tokens), keeps tables whole | LangChain TokenSplitter |
| **Embedder** | Converts text to vectors (384-dim) | SentenceTransformer |
| **Vector DB** | Stores & searches embeddings | Qdrant (Docker) |
| **Metadata DB** | Stores document structure | PostgreSQL (Docker) |
| **Hybrid Retriever** | Combines dense + sparse search | Qdrant + BM25 + RRF |
| **Reranker** | Ranks results by relevance | CrossEncoder |
| **LLM** | Generates answers | Grok (xAI API) |
| **UI** | Query interface | Streamlit |

---

## 📊 Typical Workflow

```
PDF/DOCX Files
    ↓ [Parser]
Elements (text, tables)
    ↓ [Chunker]
Chunks with metadata
    ↓ [Embedder]
Vectors (384-dim)
    ↓
┌─────────────────┐
│ Qdrant (Dense)  │  PostgreSQL (Meta)
│ Vector Search   │  Chunk Content
└─────────────────┘
    ↓
Hybrid Retrieval + RRF
    ↓
Top 20 Results
    ↓ [Reranker]
Top 5 Results
    ↓ [Grok LLM]
Answer + Citations
    ↓
Streamlit UI
```

---

## 🎯 Performance Baselines

| Operation | Time | Notes |
|-----------|------|-------|
| Model download | 2-3 min | First run only, cached after |
| Parse PDF (2 pages) | 2-3 sec | With hi_res strategy |
| Embed chunk | ~10 ms | Batch size 64 |
| Ingest 1000 chunks | 2-3 min | Includes parse + embed + store |
| Query latency | 2-5 sec | Retrieval + reranking + generation |
| Storage per 1000 chunks | ~50 MB | Vectors + metadata + indices |

---

## 🐛 Common Issues & Fixes

### Issue: "No such file or directory: .env"
**Fix:** Ensure you're in the `barc_rag/` directory when running.

### Issue: "ConnectionRefusedError: PostgreSQL"
**Fix:** Wait 15 seconds after `docker-compose up`, then restart:
```bash
docker-compose restart postgres
```

### Issue: Model download fails
**Fix:** Ensure stable internet. The system auto-caches with HuggingFace.

### Issue: "xAI API key invalid"
**Fix:** Double-check your API key in `.env` (no extra spaces/newlines).

### Issue: Query takes >10 seconds
**Fix:** Reduce `BATCH_SIZE` in `config.py` to 32 (uses less RAM).

---

## 📚 Advanced Usage

### Command-Line Ingestion

```python
from ingest.ingest_pipeline import IngestPipeline

pipeline = IngestPipeline()
stats = pipeline.ingest_directory("./documents")
print(f"Ingested {stats['ingested_files']} files")
```

### Direct Query (Python)

```python
from pipeline.rag_pipeline import RAGPipeline

rag = RAGPipeline()
result = rag.query("What is X?")
print(result["answer"])
print([c["payload"]["source_file"] for c in result["source_chunks"]])
```

### Check Database Status

```bash
docker exec -it barc_postgres psql -U barc_user -d barc_rag -c "SELECT COUNT(*) FROM chunks;"
```

---

## 🔌 System Architecture

### Data Flow
1. User uploads documents → Stored in `documents/`
2. Click "Start Ingestion" → System processes files
3. Documents parsed → Elements extracted
4. Elements chunked → Vectors generated
5. Vectors stored in Qdrant, metadata in PostgreSQL
6. User asks question → Hybrid search retrieves chunks
7. Chunks reranked → Top 5 sent to Grok
8. Grok generates answer → Displayed with sources

### Databases

**Qdrant** (Vector DB)
- Cosine distance similarity
- 384-dim vectors
- Returns top-K similar chunks

**PostgreSQL** (Metadata DB)
- Stores document info (filename, pages)
- Stores chunk content (for BM25 indexing)
- References back to Qdrant vectors

---

## 💡 Tips & Tricks

### Optimize for Large Collections

Edit `config.py`:
```python
BATCH_SIZE = 32              # Lower = less RAM, slower
HYBRID_RETRIEVAL_TOP_K = 10  # Lower = faster, less comprehensive
CHUNK_SIZE = 256             # Lower = more chunks, slower ingestion
```

### Monitor Ingestion Progress

```bash
tail -f ingest_log.db  # Check what's been ingested
sqlite3 ingest_log.db "SELECT COUNT(*) FROM ingested_files;"
```

### View Database Schema

```bash
# Connect to PostgreSQL
docker exec -it barc_postgres psql -U barc_user -d barc_rag

# List tables
\dt

# View chunks
SELECT chunk_id, type, page_number FROM chunks LIMIT 5;
```

### Export Query Results

```python
from pipeline.rag_pipeline import RAGPipeline
import json

rag = RAGPipeline()
result = rag.query("Your question")
with open("result.json", "w") as f:
    json.dump(result, f, indent=2)
```

---

## 🛑 Stopping & Cleanup

### Stop Services
```bash
docker-compose down
```

### Stop + Remove Data
```bash
docker-compose down -v
rm -rf qdrant_storage pg_data ingest_log.db
```

### Stop + Keep Data
```bash
docker-compose stop
```

### Restart Services
```bash
docker-compose restart
```

---

## 📖 Learn More

- **Unstructured Docs**: https://docs.unstructured.io/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **SentenceTransformers**: https://www.sbert.net/
- **xAI Grok API**: https://docs.x.ai/
- **Streamlit**: https://docs.streamlit.io/

---

## 🆘 Need Help?

Check these in order:
1. **Docker logs**: `docker-compose logs postgres` / `docker-compose logs qdrant`
2. **Streamlit console**: Check the terminal running `streamlit run app/main.py`
3. **API key**: Verify in `.env` (no extra whitespace)
4. **.env file**: Ensure all required variables are set
5. **Network**: Check internet connection for model downloads

---

**Enjoy your multimodal RAG system! 🚀**
