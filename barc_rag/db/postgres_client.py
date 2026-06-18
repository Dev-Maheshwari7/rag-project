"""
PostgreSQL database client for managing document metadata and chunks.
"""

import psycopg2
from typing import List, Dict, Any, Optional

from config import POSTGRES_DSN


class PostgresDB:
    """Manage PostgreSQL database operations."""

    def __init__(self):
        """Initialize database connection and create tables if needed."""
        self.dsn = POSTGRES_DSN
        self._create_tables()

    def _get_connection(self):
        """Get a database connection."""
        return psycopg2.connect(self.dsn)

    def _create_tables(self):
        """Create required tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                total_pages INT,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL REFERENCES documents(doc_id),
                type TEXT NOT NULL,
                page_number INT,
                content TEXT NOT NULL,
                original_content TEXT,
                token_count INT,
                source_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Safely add original_content if table already existed without it
        cursor.execute("""
            ALTER TABLE chunks ADD COLUMN IF NOT EXISTS original_content TEXT
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("PostgreSQL tables initialized")

    def insert_document(self, doc_metadata: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO documents (doc_id, filename, total_pages)
            VALUES (%s, %s, %s)
            ON CONFLICT (doc_id) DO NOTHING
        """, (
            doc_metadata["doc_id"],
            doc_metadata["filename"],
            doc_metadata.get("total_pages")
        ))

        conn.commit()
        cursor.close()
        conn.close()

    def insert_chunks(self, chunks: List[Dict[str, Any]]):
        conn = self._get_connection()
        cursor = conn.cursor()

        for chunk in chunks:
            cursor.execute("""
                INSERT INTO chunks (chunk_id, doc_id, type, page_number, content, original_content, token_count, source_file)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (chunk_id) DO NOTHING
            """, (
                chunk["chunk_id"],
                chunk["doc_id"],
                chunk["type"],
                chunk["page_number"],
                chunk["content"],
                chunk.get("original_content"),
                chunk["token_count"],
                chunk["source_file"]
            ))

        conn.commit()
        cursor.close()
        conn.close()

    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, doc_id, type, page_number, content, original_content, token_count, source_file
            FROM chunks WHERE chunk_id = %s
        """, (chunk_id,))

        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return {
                "chunk_id": row[0],
                "doc_id": row[1],
                "type": row[2],
                "page_number": row[3],
                "content": row[4],
                "original_content": row[5],
                "token_count": row[6],
                "source_file": row[7]
            }
        return None

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT chunk_id, doc_id, type, page_number, content, original_content, token_count, source_file
            FROM chunks
        """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return [{
            "chunk_id": row[0],
            "doc_id": row[1],
            "type": row[2],
            "page_number": row[3],
            "content": row[4],
            "original_content": row[5],
            "token_count": row[6],
            "source_file": row[7]
        } for row in rows]

    def get_stats(self) -> Dict[str, Any]:
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documents")
        doc_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "total_documents": doc_count,
            "total_chunks": chunk_count
        }