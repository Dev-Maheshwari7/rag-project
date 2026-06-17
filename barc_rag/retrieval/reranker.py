"""
Reranker module using cross-encoders for ranking retrieved chunks.
"""

from typing import List, Dict, Any
from sentence_transformers import CrossEncoder

from config import CROSSENCODER_MODEL, RERANKER_TOP_K


class Reranker:
    """Rerank retrieved chunks using cross-encoders."""

    def __init__(self, model_name: str = CROSSENCODER_MODEL):
        """
        Initialize reranker with a cross-encoder model.

        Args:
            model_name: Cross-encoder model name (auto-downloaded by HuggingFace)
        """
        self.model = CrossEncoder(model_name)

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = RERANKER_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates based on relevance to query.

        Args:
            query: Query string
            candidates: List of candidate chunks to rerank
            top_k: Number of top chunks to return

        Returns:
            Top K reranked chunks with scores
        """
        if not candidates:
            return []

        # Extract content from candidates
        candidate_texts = [
            c["payload"].get("content", "") if "payload" in c else c.get("content", "")
            for c in candidates
        ]

        # Score (query, candidate) pairs
        scores = self.model.predict([(query, text) for text in candidate_texts])

        # Add scores to candidates
        ranked_candidates = []
        for candidate, score in zip(candidates, scores):
            ranked_candidates.append({
                **candidate,
                "rerank_score": float(score)
            })

        # Sort by rerank score descending
        ranked_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        return ranked_candidates[:top_k]
