"""
Embedding module for generating vector embeddings.
Uses SentenceTransformer to embed chunks.
"""

from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np

from llm.grok_client import GrokClient


class Embedder:
    """Generate embeddings for text chunks."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", batch_size: int = 64):
        """
        Initialize embedder with a SentenceTransformer model.

        Args:
            model_name: Model name (will be auto-downloaded and cached by HuggingFace)
            batch_size: Batch size for embedding
        """
        self.model = SentenceTransformer(model_name)
        self.batch_size = batch_size
        self.grok = GrokClient()  # For table summarization

    def _summarize_table(self, html_content: str) -> str:
        """
        Summarize a table using Grok API.

        Args:
            html_content: Raw HTML table content

        Returns:
            2-3 sentence summary of the table
        """
        try:
            prompt = f"Summarize this table in 2-3 sentences describing what data it contains and its key values:\n{html_content}"
            # Call Grok with minimal context
            response = self.grok.client.chat.completions.create(
                model=self.grok.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            summary = response.choices[0].message.content.strip()
            return summary
        except Exception as e:
            print(f"Failed to summarize table: {e}. Using fallback.")
            # Fallback: extract first 100 chars
            return html_content[:100] + "..."

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> tuple:
        """
        Embed a list of chunks. For tables, summarize first then embed the summary.

        Args:
            chunks: List of chunk dicts with 'content' key

        Returns:
            Tuple of:
            - List of (chunk_id, embedding, metadata) tuples for Qdrant
            - List of processed chunks (with original_content) for PostgreSQL
        """
        # Process chunks: summarize tables
        processed_chunks = []
        for chunk in chunks:
            if chunk["type"] == "table":
                # Summarize table and store original
                print(f"[DEBUG] Summarizing table chunk: {chunk['chunk_id']}")
                summary = self._summarize_table(chunk["content"])
                print(f"[DEBUG] Table summary: {summary[:100]}...")
                chunk["original_content"] = chunk["content"]  # Store raw HTML
                chunk["content"] = summary  # Replace with summary for embedding
            else:
                # Text chunks: no original_content needed
                chunk["original_content"] = None
            processed_chunks.append(chunk)

        # Extract content for embedding
        contents = [chunk["content"] for chunk in processed_chunks]

        # Batch embed
        embeddings = self.model.encode(contents, batch_size=self.batch_size, convert_to_tensor=False)

        # Convert numpy arrays to lists and pair with metadata
        embedding_results = []
        for i, chunk in enumerate(processed_chunks):
            embedding = embeddings[i].tolist() if isinstance(embeddings[i], np.ndarray) else embeddings[i]

            metadata = {
                "doc_id": chunk["doc_id"],
                "type": chunk["type"],
                "page_number": chunk["page_number"],
                "source_file": chunk["source_file"],
                "content": chunk["content"],
                "token_count": chunk["token_count"],
                "original_content": chunk.get("original_content")
            }

            embedding_results.append((chunk["chunk_id"], embedding, metadata))

        return embedding_results, processed_chunks


    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query string.

        Args:
            query: Query text

        Returns:
            Embedding as list of floats
        """
        embedding = self.model.encode(query, convert_to_tensor=False)
        return embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
