# BARC RAG System - Testing & Validation Guide

## Pre-Flight Checks

### 1. Environment Validation

```bash
# Check Python version
python --version
# Expected: Python 3.9+

# Check Docker
docker --version
docker-compose --version

# Check .env exists
cat .env
# Should show: XAI_API_KEY, POSTGRES_USER, etc.

# Verify all directories exist
ls -la
# Expected: ingest/, db/, retrieval/, llm/, pipeline/, app/, documents/
```

### 2. Docker Services Validation

```bash
# Start services
docker-compose up -d

# Verify running
docker ps
# Expected: qdrant and barc_postgres containers

# Check Qdrant health
curl http://localhost:6333/health
# Expected: 200 OK response

# Check PostgreSQL
docker exec -it barc_postgres psql -U barc_user -d barc_rag -c "SELECT version();"
# Expected: PostgreSQL version

# Check network
docker network ls
# Expected: rag_network exists
```

### 3. Dependency Validation

```bash
# Install requirements
pip install -r requirements.txt

# Verify installations
python -c "import sentence_transformers; print('✓ SentenceTransformer OK')"
python -c "import qdrant_client; print('✓ Qdrant client OK')"
python -c "import psycopg2; print('✓ PostgreSQL client OK')"
python -c "import unstructured; print('✓ Unstructured OK')"
python -c "import streamlit; print('✓ Streamlit OK')"
python -c "import openai; print('✓ OpenAI SDK OK')"
```

### 4. Configuration Validation

```bash
# Test config loading
python -c "from config import *; print(f'XAI_BASE_URL: {XAI_BASE_URL}'); print(f'QDRANT_HOST: {QDRANT_HOST}'); print(f'POSTGRES_DSN: {POSTGRES_DSN}')"
```

## Functional Testing

### Test 1: Database Connectivity

```python
# test_db_connection.py
from db.qdrant_client import QdrantDB
from db.postgres_client import PostgresDB

# Test Qdrant
try:
    qdrant = QdrantDB()
    info = qdrant.get_collection_info()
    print(f"✓ Qdrant connected. Points: {info['points_count']}")
except Exception as e:
    print(f"✗ Qdrant connection failed: {e}")

# Test PostgreSQL
try:
    postgres = PostgresDB()
    stats = postgres.get_stats()
    print(f"✓ PostgreSQL connected. Documents: {stats['total_documents']}, Chunks: {stats['total_chunks']}")
except Exception as e:
    print(f"✗ PostgreSQL connection failed: {e}")
```

Run:
```bash
python test_db_connection.py
```

### Test 2: Embedding Generation

```python
# test_embeddings.py
from ingest.embedder import Embedder

try:
    embedder = Embedder()
    
    # Test query embedding
    query_embedding = embedder.embed_query("What is machine learning?")
    print(f"✓ Query embedding generated: shape {len(query_embedding)}")
    
    # Test batch embedding
    test_chunks = [
        {"chunk_id": "test_1", "content": "This is a test chunk", 
         "doc_id": "test.pdf", "type": "text", "page_number": 1, "token_count": 5},
        {"chunk_id": "test_2", "content": "Another test chunk",
         "doc_id": "test.pdf", "type": "text", "page_number": 2, "token_count": 4}
    ]
    
    embeddings = embedder.embed_chunks(test_chunks)
    print(f"✓ Batch embedding generated: {len(embeddings)} chunks")
    print(f"  - Embedding dimensions: {len(embeddings[0][1])}")
except Exception as e:
    print(f"✗ Embedding test failed: {e}")
```

Run:
```bash
python test_embeddings.py
```

### Test 3: Document Parsing

```python
# test_parser.py
from pathlib import Path
from ingest.parser import parse_document

# Create a test PDF (use any existing PDF)
test_files = list(Path("documents").glob("*.pdf"))

if test_files:
    try:
        elements = parse_document(str(test_files[0]))
        print(f"✓ Parsed {test_files[0].name}: {len(elements)} elements")
        for elem in elements[:3]:
            print(f"  - {elem['type']}: {elem['content'][:50]}...")
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
else:
    print("⚠ No PDFs found in documents/ folder. Add some to test parsing.")
```

Run:
```bash
python test_parser.py
```

### Test 4: Chunking

```python
# test_chunking.py
from ingest.chunker import chunk_elements

# Test with sample elements
test_elements = [
    {
        "type": "text",
        "content": "This is a long text that will be chunked. " * 50,  # Long text
        "page_number": 1,
        "source_file": "test.pdf"
    },
    {
        "type": "table",
        "content": "<table><tr><td>Cell 1</td><td>Cell 2</td></tr></table>",
        "page_number": 2,
        "source_file": "test.pdf"
    }
]

try:
    chunks = chunk_elements(test_elements)
    print(f"✓ Chunking successful: {len(chunks)} chunks created")
    for chunk in chunks:
        print(f"  - {chunk['type']}: {len(chunk['content'])} chars, {chunk['token_count']} tokens")
except Exception as e:
    print(f"✗ Chunking failed: {e}")
```

Run:
```bash
python test_chunking.py
```

### Test 5: Hybrid Retrieval

```python
# test_retrieval.py
from retrieval.hybrid_retriever import HybridRetriever

try:
    retriever = HybridRetriever()
    
    # Test with sample query (assuming some data is indexed)
    results = retriever.retrieve("test query", top_k=5)
    
    if results:
        print(f"✓ Hybrid retrieval successful: {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result.get('rrf_score', result.get('score', 0)):.4f}")
    else:
        print("⚠ No results found. Try ingesting documents first.")
except Exception as e:
    print(f"✗ Retrieval failed: {e}")
```

Run:
```bash
python test_retrieval.py
```

### Test 6: Reranking

```python
# test_reranking.py
from retrieval.reranker import Reranker

try:
    reranker = Reranker()
    
    # Test candidates
    test_candidates = [
        {
            "payload": {
                "content": "Machine learning is a subset of AI",
                "type": "text",
                "source_file": "test.pdf",
                "page_number": 1
            }
        },
        {
            "payload": {
                "content": "Deep learning uses neural networks",
                "type": "text",
                "source_file": "test.pdf",
                "page_number": 2
            }
        }
    ]
    
    ranked = reranker.rerank("What is machine learning?", test_candidates, top_k=2)
    print(f"✓ Reranking successful: {len(ranked)} results")
    for i, result in enumerate(ranked, 1):
        print(f"  {i}. Score: {result.get('rerank_score', 0):.4f}")
except Exception as e:
    print(f"✗ Reranking failed: {e}")
```

Run:
```bash
python test_reranking.py
```

### Test 7: LLM Generation

```python
# test_grok.py
from llm.grok_client import GrokClient

try:
    grok = GrokClient()
    
    # Test context
    test_chunks = [
        {
            "payload": {
                "type": "text",
                "content": "Python is a high-level programming language",
                "source_file": "guide.pdf",
                "page_number": 1
            }
        }
    ]
    
    answer = grok.generate("What is Python?", test_chunks)
    print(f"✓ LLM generation successful:")
    print(f"  {answer}")
except Exception as e:
    print(f"✗ LLM generation failed: {e}")
    print("  Check: Is XAI_API_KEY set correctly in .env?")
```

Run:
```bash
python test_grok.py
```

### Test 8: Full RAG Pipeline

```python
# test_rag_pipeline.py
from pipeline.rag_pipeline import RAGPipeline

try:
    rag = RAGPipeline()
    
    # Test query
    result = rag.query("What is the main topic?")
    
    print(f"✓ RAG pipeline executed successfully")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nSources: {len(result['source_chunks'])} chunks")
    print(f"Documents: {result['doc_ids']}")
except Exception as e:
    print(f"✗ RAG pipeline failed: {e}")
```

Run:
```bash
python test_rag_pipeline.py
```

## Integration Testing

### Test Complete Workflow

```bash
# 1. Start fresh
docker-compose down
docker-compose up -d
sleep 15

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ingest sample documents
python -c "
from ingest.ingest_pipeline import IngestPipeline
pipeline = IngestPipeline()
stats = pipeline.ingest_directory('./documents')
print(f'Ingested: {stats[\"ingested_files\"]} files, {stats[\"total_chunks\"]} chunks')
"

# 4. Run query
python -c "
from pipeline.rag_pipeline import RAGPipeline
rag = RAGPipeline()
result = rag.query('Your test question')
print(result['answer'])
"

# 5. Launch UI
streamlit run app/main.py
```

## Performance Benchmarks

### Expected Performance on Developer Laptop

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| Model download | 2-3 min | First run only, cached |
| Parse PDF (2 pages, hi_res) | 2-3 sec | Tables extracted |
| Embed 100 chunks | 1-2 sec | Batch size 64 |
| Ingest 100 PDFs | 5-10 min | Full pipeline |
| Dense search (Qdrant) | 50-100 ms | Top 20 |
| Sparse search (BM25) | 100-200 ms | Top 20 |
| Reranking 20 results | 500 ms | CrossEncoder |
| LLM generation (Grok) | 1-2 sec | Network dependent |
| **Total query latency** | **2-5 sec** | End-to-end |

## Load Testing

### Test with Multiple Queries

```bash
# test_load.py
from pipeline.rag_pipeline import RAGPipeline
import time

rag = RAGPipeline()

queries = [
    "What is the main topic?",
    "Summarize the findings",
    "What data is in the tables?",
    "How does this relate to X?",
    "What are the key points?"
]

for query in queries:
    start = time.time()
    result = rag.query(query)
    latency = time.time() - start
    print(f"Query: {query[:30]}... | Latency: {latency:.2f}s | Sources: {len(result['source_chunks'])}")
```

## Validation Checklist

- [ ] All Docker containers running
- [ ] Database connectivity confirmed
- [ ] Models cached on disk
- [ ] Embeddings generated correctly
- [ ] Parser extracts text and tables
- [ ] Chunks created with correct sizes
- [ ] Hybrid search returns results
- [ ] Reranking improves relevance
- [ ] Grok API responds correctly
- [ ] Full pipeline executes end-to-end
- [ ] Streamlit UI loads without errors
- [ ] Ingestion completes without failures
- [ ] Query latency acceptable (<5 sec)
- [ ] Source citations accurate
- [ ] No memory leaks after extended use

## Troubleshooting Issues

### Issue: "Module not found"
```bash
# Ensure you're in the right directory
cd barc_rag

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### Issue: "CUDA out of memory"
```bash
# Not using GPU by default, but if you are:
# Reduce batch size in config.py
BATCH_SIZE = 32
```

### Issue: "Slow queries"
```python
# Check what's taking time
import time
from pipeline.rag_pipeline import RAGPipeline

rag = RAGPipeline()

# Test dense search only
start = time.time()
dense = rag.retriever.qdrant.search(embedding_vector, top_k=20)
print(f"Dense search: {time.time() - start:.2f}s")

# Test sparse search only
start = time.time()
sparse = rag.retriever.bm25.get_scores(tokens)
print(f"Sparse search: {time.time() - start:.2f}s")

# Test reranking
start = time.time()
reranked = rag.reranker.rerank(query, results)
print(f"Reranking: {time.time() - start:.2f}s")

# Test LLM
start = time.time()
answer = rag.llm.generate(query, reranked)
print(f"LLM: {time.time() - start:.2f}s")
```

### Issue: "Low relevance results"
```python
# Tune hybrid search weights
# Adjust RRF_K in config.py (currently 60)
# Lower k = more weight on relevance
# Higher k = more balanced retrieval
```

---

**Testing Complete** ✅

Use these tests to validate your installation and troubleshoot issues.
