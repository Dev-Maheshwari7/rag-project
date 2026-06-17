"""
Grok LLM client using Groq API via OpenAI SDK.
"""

from typing import List, Dict, Any
from openai import OpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, GROK_MODEL


class GrokClient:
    """Interface with Grok LLM via Groq API."""

    def __init__(self, api_key: str = GROQ_API_KEY, base_url: str = GROQ_BASE_URL, model: str = GROK_MODEL):
        """
        Initialize Grok client using OpenAI SDK with Groq endpoint.

        Args:
            api_key: Groq API key
            base_url: Groq API base URL
            model: Model name (default: mixtral-8x7b-32768)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def generate(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """
        Generate answer based on query and context chunks.

        Args:
            query: User query string
            context_chunks: List of context chunks with 'payload' containing 'type' and 'content'

        Returns:
            Generated answer string
        """
        # Format context
        formatted_context = self._format_context(context_chunks)

        # System prompt
        system_prompt = (
            "You are a helpful assistant. Answer only using the provided context. "
            "If the answer is not present in the context, say 'I don't know'. "
            "Do not make up information."
        )

        # User prompt
        user_prompt = f"""Context:
{formatted_context}

Question: {query}

Answer:"""

        # Call Grok API
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Format chunks for inclusion in prompt.

        Args:
            chunks: List of context chunks

        Returns:
            Formatted context string
        """
        formatted_parts = []

        for i, chunk in enumerate(chunks, 1):
            payload = chunk.get("payload", {})
            chunk_type = payload.get("type", "text")
            content = payload.get("content", "")
            source = payload.get("source_file", "unknown")
            page = payload.get("page_number", "unknown")

            # Add type label
            type_label = "[TABLE]" if chunk_type == "table" else "[TEXT]"

            formatted_parts.append(
                f"{type_label} (Source: {source}, Page: {page})\n{content}"
            )

        return "\n\n".join(formatted_parts)
