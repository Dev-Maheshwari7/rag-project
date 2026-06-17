"""
Embedding module for generating vector embeddings.
Uses SentenceTransformer to embed chunks.
"""

from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np


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

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Tuple[str, List[float], Dict[str, Any]]]:
        """
        Embed a list of chunks.

        Args:
            chunks: List of chunk dicts with 'content' key

        Returns:
            List of tuples: (chunk_id, embedding, metadata)
            where embedding is a list of floats and metadata contains chunk info
        """
        # Extract content for embedding
        contents = [chunk["content"] for chunk in chunks]

        # Batch embed
        embeddings = self.model.encode(contents, batch_size=self.batch_size, convert_to_tensor=False)

        # Convert numpy arrays to lists and pair with metadata
        results = []
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i].tolist() if isinstance(embeddings[i], np.ndarray) else embeddings[i]

            metadata = {
                "doc_id": chunk["doc_id"],
                "type": chunk["type"],
                "page_number": chunk["page_number"],
                "source_file": chunk["source_file"],
                "content": chunk["content"],
                "token_count": chunk["token_count"]
            }

            results.append((chunk["chunk_id"], embedding, metadata))

        return results

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
