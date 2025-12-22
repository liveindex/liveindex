"""
Query pipeline: Embed → Search → Format with Sources

This module handles vector search queries against the document index.
"""

import os
import time
import logging
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from embeddings import get_embedding

logger = logging.getLogger(__name__)

# Configuration
COLLECTION_NAME = "documents"


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port)


async def search_documents(query: str, top_k: int = 5) -> Dict:
    """
    Search for documents matching the query.

    Args:
        query: The search query
        top_k: Number of results to return

    Returns:
        dict with search results including sources and latency
    """
    start_time = time.time()

    client = get_qdrant_client()

    # Check if collection exists
    try:
        client.get_collection(COLLECTION_NAME)
    except UnexpectedResponse:
        logger.warning(f"Collection '{COLLECTION_NAME}' does not exist")
        return {
            "answer": "No documents have been indexed yet. Please ingest documents first.",
            "sources": [],
            "latency_ms": (time.time() - start_time) * 1000,
        }

    # Get embedding for the query
    query_embedding = await get_embedding(query)

    # Search Qdrant
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding,
        limit=top_k,
        with_payload=True,
    )

    if not search_results:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "answer": "No relevant documents found for your query.",
            "sources": [],
            "latency_ms": elapsed_ms,
        }

    # Format sources
    sources = []
    context_chunks = []

    for result in search_results:
        payload = result.payload
        sources.append({
            "file": payload.get("file_path", "unknown"),
            "chunk": payload.get("chunk_text", ""),
            "score": round(result.score, 4),
            "updated_at": payload.get("updated_at", ""),
        })
        context_chunks.append(payload.get("chunk_text", ""))

    # Build answer from top results
    # For now, we return the most relevant chunk as the answer
    # In a production system, you'd use an LLM to synthesize an answer
    top_chunk = context_chunks[0] if context_chunks else ""

    # Create a simple answer by highlighting the most relevant content
    answer = generate_answer(query, context_chunks)

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(f"Query '{query[:50]}...' returned {len(sources)} results in {elapsed_ms:.1f}ms")

    return {
        "answer": answer,
        "sources": sources,
        "latency_ms": round(elapsed_ms, 2),
    }


def generate_answer(query: str, context_chunks: List[str]) -> str:
    """
    Generate an answer from the retrieved context chunks.

    For the demo, we use a simple extraction approach.
    In production, this would use an LLM to synthesize the answer.

    Args:
        query: The user's query
        context_chunks: Retrieved text chunks

    Returns:
        Generated answer string
    """
    if not context_chunks:
        return "No relevant information found."

    # For demo purposes, return the top chunk with context
    # This could be enhanced with an LLM call for better answers
    top_chunk = context_chunks[0]

    # Clean up the chunk for presentation
    answer = top_chunk.strip()

    # If we have multiple relevant chunks, indicate there's more
    if len(context_chunks) > 1:
        answer += f"\n\n[{len(context_chunks) - 1} additional relevant sections found]"

    return answer


async def get_document_count() -> int:
    """Get the total number of indexed document chunks."""
    client = get_qdrant_client()

    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        return collection_info.points_count
    except UnexpectedResponse:
        return 0


async def get_unique_documents() -> List[str]:
    """Get list of unique document file paths in the index."""
    client = get_qdrant_client()

    try:
        # Scroll through all points to get unique file paths
        # For large indexes, this should be paginated
        results = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=["file_path"],
        )

        file_paths = set()
        for point in results[0]:
            if point.payload and "file_path" in point.payload:
                file_paths.add(point.payload["file_path"])

        return sorted(list(file_paths))
    except UnexpectedResponse:
        return []
