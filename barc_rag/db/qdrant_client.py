"""
Qdrant vector database client for managing document embeddings.
"""

from typing import List, Tuple, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from config import QDRANT_HOST, QDRANT_PORT, COLLECTION_NAME, VECTOR_SIZE


class QdrantDB:
    """Manage Qdrant vector database operations."""

    def __init__(self):
        """Initialize Qdrant client and create collection if needed."""
        self.client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        self.collection_name = COLLECTION_NAME
        self._create_collection()

    def _create_collection(self):
        """Create collection if it doesn't exist."""
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
            )
            print(f"Created Qdrant collection: {self.collection_name}")

    def upsert_chunks(self, chunks_with_embeddings: List[Tuple[str, List[float], Dict[str, Any]]]):
        """
        Upsert chunks with embeddings to Qdrant.

        Args:
            chunks_with_embeddings: List of (chunk_id, embedding, metadata) tuples
        """
        points = []
        for chunk_id, embedding, metadata in chunks_with_embeddings:
            point = PointStruct(
                id=hash(chunk_id) & 0x7FFFFFFF,  # Convert to positive int
                vector=embedding,
                payload=metadata
            )
            points.append(point)

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_vector: List[float], top_k: int = 20, filter_: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors in Qdrant.

        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filter_: Optional filter criteria

        Returns:
            List of results: [{chunk_id, score, payload}, ...]
        """
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=filter_
        )

        return [
            {
                "chunk_id": r.payload.get("doc_id", str(r.id)),
                "score": r.score,
                "payload": r.payload
            }
            for r in results.points
        ]

    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        info = self.client.get_collection(self.collection_name)
        return {
            "points_count": info.points_count,
            "vectors_count": info.vectors_count
        }
