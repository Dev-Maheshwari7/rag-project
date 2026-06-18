"""
Main RAG pipeline orchestration.
Combines retrieval, reranking, and generation.
"""

from typing import Dict, Any, List

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.reranker import Reranker
from llm.grok_client import GrokClient
from db.postgres_client import PostgresDB


class RAGPipeline:
    """Orchestrate the full RAG pipeline."""

    def __init__(self):
        """Initialize pipeline components."""
        self.retriever = HybridRetriever()
        self.reranker = Reranker()
        self.llm = GrokClient()
        self.postgres = PostgresDB()

    def query(self, user_question: str) -> Dict[str, Any]:
        """
        Process a user query through the full RAG pipeline.

        Args:
            user_question: User's question string

        Returns:
            {
                'answer': str,
                'source_chunks': List[Dict],
                'doc_ids': List[str]
            }
        """
        # 1. Retrieve top candidates with hybrid search
        retrieved_chunks = self.retriever.retrieve(user_question, top_k=20)

        if not retrieved_chunks:
            return {
                "answer": "No relevant documents found.",
                "source_chunks": [],
                "doc_ids": []
            }

        # 2. Rerank to top 5
        reranked_chunks = self.reranker.rerank(user_question, retrieved_chunks, top_k=5)

        # 3. Prepare context: fetch original_content for tables
        context_chunks = []
        for chunk in reranked_chunks:
            chunk_id = chunk.get("chunk_id")
            chunk_type = chunk["payload"].get("type", "text")
            
            # For tables, fetch original_content from Postgres
            if chunk_type == "table":
                db_chunk = self.postgres.get_chunk_by_id(chunk_id)
                if db_chunk and db_chunk.get("original_content"):
                    chunk["payload"]["content"] = db_chunk["original_content"]
            
            context_chunks.append(chunk)

        # 4. Generate answer with Grok
        answer = self.llm.generate(user_question, context_chunks)

        # 5. Extract source information
        doc_ids = list(set([
            c["payload"].get("doc_id", "") for c in context_chunks
            if "payload" in c
        ]))

        return {
            "answer": answer,
            "source_chunks": context_chunks,
            "doc_ids": doc_ids
        }
