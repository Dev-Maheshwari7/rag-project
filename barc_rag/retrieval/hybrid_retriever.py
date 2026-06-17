"""
Hybrid retriever combining dense (Qdrant) and sparse (BM25) search with RRF fusion.
"""

from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
import numpy as np

from ingest.embedder import Embedder
from db.qdrant_client import QdrantDB
from db.postgres_client import PostgresDB
from config import HYBRID_RETRIEVAL_TOP_K, RRF_K


class HybridRetriever:
    """Hybrid retriever combining dense and sparse search."""

    def __init__(self):
        """Initialize retriever with embedder and databases."""
        self.embedder = Embedder()
        self.qdrant = QdrantDB()
        self.postgres = PostgresDB()
        self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from all chunks in Postgres."""
        print("Building BM25 index...")
        chunks = self.postgres.get_all_chunks()

        if not chunks:
            print("No chunks found in database. BM25 index will be empty.")
            self.bm25 = None
            self.chunk_id_to_content = {}
            return

        # Build corpus and mapping
        self.chunk_id_to_content = {chunk["chunk_id"]: chunk for chunk in chunks}
        corpus = [chunk["content"].split() for chunk in chunks]

        self.bm25 = BM25Okapi(corpus)
        print(f"BM25 index built with {len(chunks)} chunks")

    def retrieve(self, query: str, top_k: int = HYBRID_RETRIEVAL_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve chunks using hybrid search (dense + sparse).

        Args:
            query: Query string
            top_k: Number of results to return

        Returns:
            List of retrieved chunks with scores
        """
        # Dense search
        query_embedding = self.embedder.embed_query(query)
        dense_results = self.qdrant.search(query_embedding, top_k=top_k)

        # Sparse search (BM25)
        sparse_results = []
        if self.bm25 is not None:
            query_tokens = query.split()
            scores = self.bm25.get_scores(query_tokens)
            top_indices = np.argsort(scores)[-top_k:][::-1]  # Get top K in descending order

            chunk_ids = list(self.chunk_id_to_content.keys())
            for idx in top_indices:
                if idx < len(chunk_ids):
                    chunk_id = chunk_ids[idx]
                    score = scores[idx]
                    if score > 0:  # Only include non-zero scores
                        sparse_results.append({
                            "chunk_id": chunk_id,
                            "score": float(score),
                            "payload": self.chunk_id_to_content[chunk_id]
                        })

        # Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results, k=RRF_K)

        # Return top K fused results
        return fused_results[:top_k]

    def _reciprocal_rank_fusion(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Fuse dense and sparse results using Reciprocal Rank Fusion.

        Args:
            dense_results: Results from dense search
            sparse_results: Results from BM25 search
            k: RRF parameter (typically 60)

        Returns:
            Fused and ranked results
        """
        # Create mapping of chunk_id to RRF score
        rrf_scores = {}

        # Process dense results
        for rank, result in enumerate(dense_results, 1):
            chunk_id = result["payload"]["doc_id"] if "doc_id" in result["payload"] else result["chunk_id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank)

        # Process sparse results
        for rank, result in enumerate(sparse_results, 1):
            chunk_id = result["payload"]["doc_id"] if "doc_id" in result["payload"] else result["chunk_id"]
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank)

        # Create result list with RRF scores
        all_results_map = {}
        for result in dense_results + sparse_results:
            chunk_id = result["payload"]["doc_id"] if "doc_id" in result["payload"] else result["chunk_id"]
            if chunk_id not in all_results_map:
                all_results_map[chunk_id] = result

        # Sort by RRF score
        fused_results = [
            {
                **all_results_map[chunk_id],
                "rrf_score": rrf_scores[chunk_id]
            }
            for chunk_id in sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        ]

        return fused_results
