# BARC RAG System - Complete Architecture & Deployment Guide

## System Overview

The BARC (Bidirectional Architecture for Retrieval and Context) RAG System is a fully local multimodal retrieval-augmented generation system designed to handle large document collections with text and tabular data.

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                       (Streamlit Web App)                            │
│                                                                       │
│  ┌──────────────────┐    ┌──────────────────┐   ┌──────────────┐  │
│  │  Query Input     │    │  View Sources    │   │ DB Statistics│  │
│  │  & Results       │    │  & Citations     │   │   & Ingest   │  │
│  └──────────────────┘    └──────────────────┘   └──────────────┘  │
└────────────────────────────────────┬──────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
        ┌───────────▼──────────┐         ┌───────────▼──────────┐
        │  RAG PIPELINE LAYER  │         │  INGEST PIPELINE     │
        ├──────────────────────┤         ├──────────────────────┤
        │ • Query embedding    │         │ • Document parsing   │
        │ • Hybrid retrieval   │         │ • Chunking (512 tok) │
        │ • Reranking          │         │ • Embedding          │
        │ • Generation         │         │ • Storage            │
        └──────────┬───────────┘         └──────────┬───────────┘
                   │                                │
        ┌──────────▼──────────────────────────────▼──────────┐
        │          RETRIEVAL & RANKING LAYER                 │
        ├────────────────────────────────────────────────────┤
        │                                                    │
        │  ┌──────────────────────┐  ┌──────────────────┐   │
        │  │  Hybrid Retriever    │  │  Reranker        │   │
        │  ├──────────────────────┤  ├──────────────────┤   │
        │  │ • Dense search       │  │ • CrossEncoder   │   │
        │  │   (Qdrant vectors)   │  │ • Top-5 ranking  │   │
        │  │ • Sparse search      │  │ • Score sorting  │   │
        │  │   (BM25 index)       │  │                  │   │
        │  │ • RRF fusion (k=60)  │  │                  │   │
        │  └──────────────────────┘  └──────────────────┘   │
        │            │                        │              │
        │            └────────────┬───────────┘              │
        │                         │                          │
        └─────────────────────────┼──────────────────────────┘
                                  │
        ┌─────────────────────────┼──────────────────────┐
        │                         │                      │
    ┌───▼────────────────┐   ┌────▼──────────────────┐  │
    │  EMBEDDING LAYER   │   │  LLM LAYER           │  │
    ├────────────────────┤   ├─────────────────────┤  │
    │ SentenceTransformer│   │ Grok LLM             │  │
    │ all-MiniLM-L6-v2   │   │ (xAI API)            │  │
    │ (384-dim vectors)  │   │ model: grok-3        │  │
    └────────────────────┘   └─────────────────────┘  │
        │                         │                    │
        └─────────────────────────┼────────────────────┘
                                  │
        ┌─────────────────────────┴──────────────────────┐
        │      DATABASE LAYER (Docker Containers)       │
        ├────────────────────────────────────────────────┤
        │                                                │
        │  ┌──────────────────┐  ┌──────────────────┐   │
        │  │ QDRANT (Vector)  │  │ PostgreSQL       │   │
        │  ├──────────────────┤  ├──────────────────┤   │
        │  │ • Collection:    │  │ • documents      │   │
        │  │   barc_documents │  │   (metadata)     │   │
        │  │ • Points: chunks │  │ • chunks         │   │
        │  │ • Vectors: 384d  │  │   (content)      │   │
        │  │ • Distance:      │  │ • Indexed on     │   │
        │  │   Cosine         │  │   doc_id         │   │
        │  │ • Port: 6333     │  │ • Port: 5432     │   │
        │  │ • Volume:        │  │ • Volume:        │   │
        │  │   qdrant_storage │  │   pg_data        │   │
        │  └──────────────────┘  └──────────────────┘   │
        │                                                │
        └────────────────────────────────────────────────┘
```

## Data Flow Details

### Document Ingestion Flow

```
Input Files (./documents)
│
├─ parse_document()
│  └─ Unstructured.partition_pdf/auto()
│     ├─ Extracts: Title, NarrativeText, ListItem → text_elements
│     └─ Extracts: Table → table_elements (whole)
│
├─ chunk_elements()
│  ├─ Text: TokenTextSplitter (512 tokens, 50 overlap)
│  └─ Table: Keep as single chunk
│
├─ embed_chunks()
│  └─ SentenceTransformer("all-MiniLM-L6-v2")
│     └─ Batch encode (size 64) → 384-dim vectors
│
├─ upsert to Qdrant
│  └─ PointStruct(id, vector=embedding, payload=metadata)
│
└─ insert to PostgreSQL
   ├─ documents table (filename, page_count, timestamp)
   └─ chunks table (content, type, metadata)

Also:
└─ Log to ingest_log.db (prevents re-ingestion)
```

### Query Flow

```
User Question
│
├─ Embedding Phase
│  └─ embed_query() → 384-dim vector
│
├─ Retrieval Phase
│  ├─ Dense Search
│  │  └─ Qdrant.search(vector, top_k=20)
│  │     → Cosine similarity ranking
│  │
│  ├─ Sparse Search
│  │  └─ BM25Okapi.get_scores(query_tokens, top_k=20)
│  │     → Keyword matching ranking
│  │
│  └─ Fusion (Reciprocal Rank Fusion)
│     └─ score = 1/(60 + rank) for each source
│        → Merge and top-20 by RRF score
│
├─ Reranking Phase
│  └─ CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
│     └─ Score pairs: (query, chunk_content)
│        → Sort and top-5
│
├─ Generation Phase
│  ├─ Format context with [TEXT] and [TABLE] labels
│  └─ Call Grok API
│     ├─ System: "Answer only from context..."
│     └─ User: "Context: {...}\n\nQuestion: {...}"
│
└─ Response
   ├─ answer: Generated text
   ├─ source_chunks: Top 5 with scores
   └─ doc_ids: Referenced documents
```

## Component Responsibilities

### 1. ingest/parser.py
- **Input**: PDF/DOCX file paths
- **Output**: List of elements with type, content, page_number, metadata
- **Processing**:
  - Uses `unstructured.partition_auto()` with hi_res strategy
  - Separates text (Title, NarrativeText, ListItem) from tables
  - Preserves HTML/markdown representation of tables

### 2. ingest/chunker.py
- **Input**: Parsed elements
- **Output**: Chunks with chunk_id, doc_id, type, page_number, token_count
- **Processing**:
  - Text elements: Split to 512 tokens with 50 token overlap
  - Table elements: Keep whole (never split)
  - Preserves source file and page tracking

### 3. ingest/embedder.py
- **Input**: List of chunks with content
- **Output**: List of (chunk_id, embedding, metadata) tuples
- **Processing**:
  - Loads SentenceTransformer("all-MiniLM-L6-v2")
  - Batch encodes in groups of 64
  - Returns 384-dimensional vectors

### 4. ingest/ingest_pipeline.py
- **Input**: documents/ directory
- **Output**: Indexed documents in Qdrant and PostgreSQL
- **Processing**:
  - Walks directory recursively for PDF/DOCX
  - Skips already-ingested files (via SQLite log)
  - Orchestrates parse → chunk → embed → store
  - Provides ingestion statistics

### 5. db/qdrant_client.py
- **Responsibility**: Vector database operations
- **Methods**:
  - `_create_collection()`: Initialize with cosine distance, 384-dim
  - `upsert_chunks()`: Store vectors with metadata
  - `search()`: Retrieve top-k similar vectors
  - `get_collection_info()`: Statistics

### 6. db/postgres_client.py
- **Responsibility**: Metadata and content storage
- **Tables**:
  - `documents`: doc_id, filename, total_pages, ingested_at
  - `chunks`: chunk_id, doc_id, type, page_number, content, token_count
- **Methods**:
  - `insert_document()`: Store document metadata
  - `insert_chunks()`: Bulk insert chunks
  - `get_chunk_by_id()`: Retrieve specific chunk
  - `get_all_chunks()`: For BM25 indexing
  - `get_stats()`: Database statistics

### 7. retrieval/hybrid_retriever.py
- **Responsibility**: Combine dense and sparse search
- **Processing**:
  - Dense: Qdrant vector search (top 20)
  - Sparse: BM25Okapi search (top 20)
  - Fusion: RRF with k=60
  - Returns top-20 fused results
- **Index Building**: Loads all chunks from PostgreSQL on init

### 8. retrieval/reranker.py
- **Responsibility**: Relevance ranking
- **Processing**:
  - CrossEncoder scores (query, chunk) pairs
  - Sorts by score descending
  - Returns top-k results

### 9. llm/grok_client.py
- **Responsibility**: LLM generation
- **Processing**:
  - Uses OpenAI SDK with xAI base URL
  - Formats chunks with [TEXT]/[TABLE] labels
  - Calls grok-3 model
  - Returns generated text

### 10. pipeline/rag_pipeline.py
- **Responsibility**: Orchestrate full pipeline
- **Processing**:
  1. retrieve() → 20 candidates
  2. rerank() → 5 top results
  3. generate() → Answer with context
  - Returns answer + sources + doc_ids

### 11. app/main.py
- **Responsibility**: User interface
- **Features**:
  - Query input text area
  - Answer display
  - Expandable sources with metadata
  - Database statistics sidebar
  - Ingestion trigger button

## Configuration Management

All configuration is centralized in `config.py` and driven by `.env`:

```python
# From .env
XAI_API_KEY              # xAI authentication
POSTGRES_USER            # Database credentials
POSTGRES_PASSWORD
POSTGRES_DB
QDRANT_HOST              # Service locations
QDRANT_PORT
DOCS_DIR                 # Input documents folder

# Constants in config.py
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CROSSENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
GROK_MODEL = "grok-3"
CHUNK_SIZE = 512         # tokens
CHUNK_OVERLAP = 50       # tokens
BATCH_SIZE = 64          # for embedding
HYBRID_RETRIEVAL_TOP_K = 20
RERANKER_TOP_K = 5
RRF_K = 60
```

## Database Schema

### PostgreSQL

#### documents table
```sql
CREATE TABLE documents (
    doc_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    total_pages INT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### chunks table
```sql
CREATE TABLE chunks (
    chunk_id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL REFERENCES documents(doc_id),
    type TEXT NOT NULL,          -- 'text' or 'table'
    page_number INT,
    content TEXT NOT NULL,
    token_count INT,
    source_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Qdrant

#### Collection: barc_documents
```json
{
  "name": "barc_documents",
  "vectors_config": {
    "size": 384,
    "distance": "Cosine"
  },
  "points": [
    {
      "id": hash(chunk_id),
      "vector": [0.123, -0.456, ...],  // 384 dimensions
      "payload": {
        "doc_id": "filename",
        "type": "text|table",
        "page_number": 1,
        "source_file": "file.pdf",
        "content": "chunk text...",
        "token_count": 512
      }
    }
  ]
}
```

## Deployment Checklist

- [ ] Docker and Docker Compose installed
- [ ] Python 3.9+ installed
- [ ] `pip install -r requirements.txt` completed
- [ ] `.env` file configured with xAI API key
- [ ] `docker-compose up -d` running
- [ ] Qdrant accessible at `http://localhost:6333`
- [ ] PostgreSQL accessible at `localhost:5432`
- [ ] Documents placed in `documents/` folder
- [ ] `streamlit run app/main.py` executed
- [ ] Ingestion completed successfully
- [ ] Test query returns results

## Performance Tuning

### For Large Collections (10k+ docs)

```python
# config.py
BATCH_SIZE = 32              # Reduce memory usage
CHUNK_SIZE = 256             # Smaller chunks = more total chunks
HYBRID_RETRIEVAL_TOP_K = 10  # Less data to rerank
RERANKER_TOP_K = 3           # Return fewer results
```

### For Fast Queries

```python
# Disable reranking
# Use only dense search (comment out BM25)
# Increase cache for embeddings
```

### For Limited RAM

```python
# Docker limits
memory: 4G              # In docker-compose.yml
# Streaming embeddings (batch size 8)
```

## Monitoring & Debugging

### Check Service Health

```bash
# Verify containers running
docker ps

# Check logs
docker-compose logs postgres
docker-compose logs qdrant

# Database stats
sqlite3 ingest_log.db "SELECT COUNT(*) FROM ingested_files;"
psql -U barc_user -d barc_rag -c "SELECT COUNT(*) FROM chunks;"
```

### Monitor Ingestion

```bash
# Real-time progress
tail -f ingest_log.db

# Check PostgreSQL
docker exec -it barc_postgres psql -U barc_user -d barc_rag \
  -c "SELECT doc_id, COUNT(*) as chunks FROM chunks GROUP BY doc_id;"
```

## Scaling Considerations

### Current Limits
- **Documents**: ~20,000 PDFs/DOCX (tested)
- **Chunks**: ~200,000+ chunks
- **Storage**: 50 GB for vectors + metadata
- **Query latency**: 2-5 seconds

### Horizontal Scaling
- Add read replicas for PostgreSQL
- Use Qdrant cloud for distributed vectors
- Implement query caching layer
- Use Kafka for async ingestion

### Optimization
- Pre-filter by document type before retrieval
- Implement chunking heuristics (headings, sections)
- Cache embeddings for common queries
- Batch process ingestion with Celery/RQ

## Security Notes

- `.env` contains credentials → Add to `.gitignore`
- xAI API key never shared in logs
- PostgreSQL only accessible locally (in production, behind VPN)
- Qdrant vector data is not encrypted (use VPN in production)
- No authentication in current setup (add for production)

## Future Enhancements

1. **Multi-turn conversation** with memory
2. **Streaming responses** from Grok
3. **Custom extraction** for specific domains
4. **FastAPI wrapper** for REST access
5. **Batch query processing** with job queue
6. **Document management** (update, delete)
7. **Analytics dashboard** for usage metrics
8. **Multi-language support** with translation
9. **Web UI improvements** with advanced filtering
10. **Kubernetes deployment** for cloud

---

**Architecture Documentation Complete** ✅
