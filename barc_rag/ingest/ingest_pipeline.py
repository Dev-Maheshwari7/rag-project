"""
Main ingestion pipeline orchestrator.
Handles document parsing, chunking, embedding, and storage.
"""

import os
import sqlite3
from pathlib import Path
from typing import List
from tqdm import tqdm
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import DOCS_DIR, INGEST_LOG_DB
from ingest.parser import parse_document
from ingest.chunker import chunk_elements
from ingest.embedder import Embedder
from db.qdrant_client import QdrantDB
from db.postgres_client import PostgresDB


class IngestPipeline:
    """Orchestrate the full ingestion pipeline."""

    def __init__(self):
        """Initialize pipeline with database and embedding clients."""
        self.embedder = Embedder()
        self.qdrant = QdrantDB()
        self.postgres = PostgresDB()
        self._init_ingest_log()

    def _init_ingest_log(self):
        """Initialize SQLite log for tracking ingested files."""
        self.log_db = INGEST_LOG_DB
        conn = sqlite3.connect(self.log_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingested_files (
                filepath TEXT PRIMARY KEY,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def _is_ingested(self, filepath: str) -> bool:
        """Check if a file has already been ingested."""
        conn = sqlite3.connect(self.log_db)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM ingested_files WHERE filepath = ?", (filepath,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def _mark_ingested(self, filepath: str):
        """Mark a file as ingested."""
        conn = sqlite3.connect(self.log_db)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ingested_files (filepath) VALUES (?)", (filepath,))
        conn.commit()
        conn.close()

    def ingest_directory(self, docs_dir: str = None) -> dict:
        """
        Ingest all PDF and DOCX files from a directory recursively.

        Args:
            docs_dir: Directory to ingest from (uses DOCS_DIR from config if None)

        Returns:
            Dictionary with ingestion statistics
        """
        docs_dir = docs_dir or DOCS_DIR
        docs_path = Path(docs_dir)

        if not docs_path.exists():
            raise ValueError(f"Documents directory not found: {docs_dir}")

        # Find all PDF and DOCX files
        document_files = list(docs_path.rglob("*.pdf")) + list(docs_path.rglob("*.docx"))
        document_files = [f for f in document_files if not self._is_ingested(str(f))]

        stats = {
            "total_files": len(document_files),
            "ingested_files": 0,
            "total_chunks": 0,
            "failed_files": []
        }

        for file_path in tqdm(document_files, desc="Ingesting documents"):
            try:
                # Parse
                elements = parse_document(str(file_path))
                if not elements:
                    print(f"No elements extracted from {file_path}")
                    continue

                # Chunk
                chunks = chunk_elements(elements)

                # Embed (returns both embedding tuples for Qdrant and processed chunks for Postgres)
                chunks_with_embeddings, processed_chunks = self.embedder.embed_chunks(chunks)

                # Upsert to Qdrant
                self.qdrant.upsert_chunks(chunks_with_embeddings)

                # Insert to Postgres (use processed_chunks which have original_content)
                doc_metadata = {
                    "doc_id": file_path.name,  # Use full filename to match chunker
                    "filename": file_path.name,
                    "total_pages": max([c.get("page_number", 1) for c in processed_chunks], default=1)
                }
                self.postgres.insert_document(doc_metadata)
                self.postgres.insert_chunks(processed_chunks)

                # Mark as ingested
                self._mark_ingested(str(file_path))

                stats["ingested_files"] += 1
                stats["total_chunks"] += len(processed_chunks)

            except Exception as e:
                print(f"Error ingesting {file_path}: {e}")
                stats["failed_files"].append((str(file_path), str(e)))

        return stats
