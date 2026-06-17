# BARC Multimodal RAG System

A fully local multimodal RAG (Retrieval-Augmented Generation) system for processing large document collections (PDFs, DOCX) with text and tables, using Grok as the LLM.

## Architecture

```
User Query
    ↓
Hybrid Retriever (Dense + Sparse)
    ↓
Dense Search (Qdrant) + BM25 (Sparse)
    ↓
Reciprocal Rank Fusion (RRF)
    ↓
Reranker (Cross-Encoder)
    ↓
Grok LLM (via xAI API)
    ↓
Answer + Sources
```

## Stack

- **Document Parsing**: Unstructured (with hi_res strategy for tables)
- **Embeddings**: all-MiniLM-L6-v2 (384-dim, auto-cached by HuggingFace)
- **Vector DB**: Qdrant (self-hosted via Docker)
- **Metadata DB**: PostgreSQL (self-hosted via Docker)
- **Sparse Search**: rank_bm25 (BM25Okapi)
- **Reranker**: cross-encoder/ms-marco-MiniLM-L-6-v2
- **LLM**: Grok (xAI API, model: grok-3)
- **Orchestration**: LangChain
- **UI**: Streamlit

## Requirements

- Docker & Docker Compose
- Python 3.9+
- xAI API Key (for Grok access)
- ~10GB+ free disk space (for models, vectors, and data)
- Internet connection (downloads models on first run)

## Setup Instructions

### 1. Clone and Navigate to Project

```bash
cd barc_rag
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: First time setup will download models from HuggingFace (~2-3 GB):
- `all-MiniLM-L6-v2` (embedder)
- `cross-encoder/ms-marco-MiniLM-L-6-v2` (reranker)

### 3. Configure Environment

Edit `.env` and set your xAI API key:

```env
XAI_API_KEY=your_actual_xai_api_key_here
POSTGRES_USER=barc_user
POSTGRES_PASSWORD=barc_pass
POSTGRES_DB=barc_rag
QDRANT_HOST=localhost
QDRANT_PORT=6333
DOCS_DIR=./documents
```

### 4. Start Docker Services

```bash
docker-compose up -d
```

This starts:
- **Qdrant** (vector database) on port 6333
- **PostgreSQL** (metadata) on port 5432

Verify they're running:
```bash
docker ps
```

Wait ~10 seconds for services to fully initialize.

### 5. Prepare Documents

Place your PDF and DOCX files in the `documents/` folder:

```
barc_rag/
├── documents/
│   ├── file1.pdf
│   ├── file2.pdf
│   └── file3.docx
```

### 6. Run the App

```bash
streamlit run app/main.py
```

The app will open at `http://localhost:8501/`

## Usage

### Ingestion

1. In the Streamlit sidebar, click **🔄 Start Ingestion**
2. The system will:
   - Parse all PDFs and DOCX files
   - Extract text and table elements
   - Chunk text (512 tokens max, 50 token overlap)
   - Keep tables whole
   - Generate embeddings with all-MiniLM-L6-v2
   - Store in Qdrant (vectors) and PostgreSQL (metadata)
   - Skip already-ingested files (via SQLite log)

### Querying

1. Enter a question in the query box
2. Click **Search & Generate Answer**
3. The system will:
   - Embed your query
   - Retrieve top 20 chunks via hybrid search (dense + BM25)
   - Rerank to top 5 with cross-encoder
   - Generate answer with Grok
   - Display sources with chunk details

### Database Stats

The sidebar shows:
- **Total Documents**: Number of ingested files
- **Total Chunks**: Number of text/table chunks indexed

## Project Structure

```
barc_rag/
├── docker-compose.yml          # Docker services (Qdrant, PostgreSQL)
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
├── config.py                    # Central configuration
├── ingest/
│   ├── parser.py               # Document parsing with Unstructured
│   ├── chunker.py              # Text chunking + table preservation
│   ├── embedder.py             # Embedding generation (MiniLM)
│   └── ingest_pipeline.py      # Orchestration + resumable ingestion
├── db/
│   ├── qdrant_client.py        # Qdrant vector DB client
│   └── postgres_client.py      # PostgreSQL metadata client
├── retrieval/
│   ├── hybrid_retriever.py     # Dense + BM25 + RRF fusion
│   └── reranker.py             # Cross-encoder reranking
├── llm/
│   └── grok_client.py          # Grok LLM client (OpenAI SDK + xAI)
├── pipeline/
│   └── rag_pipeline.py         # Full RAG orchestration
├── app/
│   └── main.py                 # Streamlit UI
└── documents/                  # Input documents folder
```

## Key Features

✅ **Multimodal Support**: Text and tables
✅ **Hybrid Retrieval**: Dense (Qdrant) + Sparse (BM25) with RRF fusion
✅ **Reranking**: Cross-encoder for better relevance
✅ **Resumable Ingestion**: Skip already-processed files
✅ **All Local**: Only LLM calls go to xAI API
✅ **Scalable**: Handles ~20,000 documents
✅ **No Splitting Tables**: Tables preserved as whole chunks
✅ **Environment-Driven**: All config from `.env`

## Performance Notes

- **First run**: Model downloads take 2-3 minutes
- **Ingestion**: ~5-10 seconds per document (parsing + embedding)
- **Query latency**: ~2-5 seconds (retrieval + reranking + generation)
- **Storage**: ~50MB per 1000 chunks (vectors + metadata)

## Troubleshooting

### Docker Services Won't Start

```bash
docker-compose logs postgres
docker-compose logs qdrant
```

### PostgreSQL Connection Error

Wait 15 seconds after `docker-compose up`. If still failing:

```bash
docker-compose restart postgres
```

### Model Download Fails

The system will try `hi_res` strategy first, then fall back to `auto`. Ensure internet connection is stable.

### API Key Invalid

Verify your xAI API key in `.env` is correct:
```bash
echo $XAI_API_KEY
```

### Memory Issues

If running on limited RAM:
- Reduce `BATCH_SIZE` in `config.py` to 32
- Reduce `HYBRID_RETRIEVAL_TOP_K` to 10

## Advanced Configuration

Edit `config.py` to customize:

```python
CHUNK_SIZE = 512              # Token size for text chunks
CHUNK_OVERLAP = 50            # Token overlap
BATCH_SIZE = 64               # Embedding batch size
HYBRID_RETRIEVAL_TOP_K = 20   # Dense + BM25 retrieval depth
RERANKER_TOP_K = 5            # Final reranked results
RRF_K = 60                    # RRF parameter
```

## API Endpoints (Future)

The system can be easily extended to expose REST APIs:
- `/api/ingest` - Trigger ingestion
- `/api/query` - Query endpoint
- `/api/stats` - Database statistics

## Security Notes

- Store `.env` safely (contains DB credentials)
- xAI API key is only used for LLM calls
- All document data stays local in Docker volumes
- PostgreSQL is only accessible locally (no external ports exposed by default)

## Cleanup

To stop and remove all services:

```bash
docker-compose down
```

To also remove persistent data:

```bash
docker-compose down -v
rm -rf qdrant_storage pg_data ingest_log.db
```

## Future Enhancements

- [ ] Streaming LLM responses
- [ ] Multi-turn conversation memory
- [ ] Custom metadata filtering
- [ ] Configurable chunking strategies
- [ ] FastAPI wrapper for REST access
- [ ] Web UI improvements
- [ ] Document deletion/updates
- [ ] Batch query processing
- [ ] Semantic caching

## License

MIT

## Support

For issues or questions:
1. Check Docker logs: `docker-compose logs`
2. Check Streamlit console output
3. Verify `.env` configuration
4. Ensure all services are running: `docker ps`
