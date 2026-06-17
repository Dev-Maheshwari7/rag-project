import os
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

# XAI API Configuration (changed to Groq)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_api_key_here")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROK_MODEL = "llama-3.1-8b-instant"

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "barc_documents"
VECTOR_SIZE = 384

# PostgreSQL Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER", "barc_user")
POSTGRES_PASSWORD = quote(os.getenv("POSTGRES_PASSWORD", "barc_pass"), safe="")
POSTGRES_DB = os.getenv("POSTGRES_DB", "barc_rag")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_DSN = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Model Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CROSSENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Document Processing
DOCS_DIR = os.getenv("DOCS_DIR", "./documents")
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens
BATCH_SIZE = 64

# Retrieval Configuration
HYBRID_RETRIEVAL_TOP_K = 20
RERANKER_TOP_K = 5
RRF_K = 60

# Ingest Log
INGEST_LOG_DB = "ingest_log.db"
