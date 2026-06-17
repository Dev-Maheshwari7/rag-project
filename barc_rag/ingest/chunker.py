"""
Chunking module for processing parsed documents.
Handles text chunking with overlap and keeps tables whole.
"""

import uuid
from typing import List, Dict, Any
from langchain_text_splitters import TokenTextSplitter


def chunk_elements(elements: List[Dict[str, Any]], chunk_size: int = 512, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunk parsed elements into chunks suitable for embedding.
    Text elements are chunked with overlap, table elements are kept whole.

    Args:
        elements: List of parsed elements from parser.parse_document()
        chunk_size: Max tokens per chunk (for text)
        chunk_overlap: Token overlap between chunks (for text)

    Returns:
        List of chunks: [
            {
                'chunk_id': str,
                'doc_id': str,
                'type': 'text' | 'table',
                'page_number': int,
                'source_file': str,
                'content': str,
                'token_count': int
            }
        ]
    """
    chunks = []
    splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for element in elements:
        if element["type"] == "text":
            # Chunk text elements
            text_chunks = splitter.split_text(element["content"])

            for text_chunk in text_chunks:
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "doc_id": element["source_file"],  # Use filename as doc_id for now
                    "type": "text",
                    "page_number": element["page_number"],
                    "source_file": element["source_file"],
                    "content": text_chunk,
                    "token_count": len(text_chunk.split())  # Approximate token count
                })

        elif element["type"] == "table":
            # Keep table as a single chunk
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "doc_id": element["source_file"],
                "type": "table",
                "page_number": element["page_number"],
                "source_file": element["source_file"],
                "content": element["content"],
                "token_count": len(element["content"].split())
            })

    return chunks
