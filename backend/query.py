"""
Query pipeline: Embed → Search → LLM Answer → Format with Sources

This module handles vector search queries against the document index
and generates answers using GPT-4o-mini.
"""

import os
import time
import logging
from typing import List, Dict, Optional

from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv

from embeddings import get_embedding

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize OpenAI client for answer generation
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
LLM_MODEL = "gpt-4o-mini"

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

    # Generate answer using LLM
    answer = await generate_answer(query, context_chunks, sources)

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info(f"Query '{query[:50]}...' returned {len(sources)} results in {elapsed_ms:.1f}ms")

    return {
        "answer": answer,
        "sources": sources,
        "latency_ms": round(elapsed_ms, 2),
    }


async def generate_answer(query: str, context_chunks: List[str], sources: List[Dict]) -> str:
    """
    Generate an answer from the retrieved context chunks using GPT-4o-mini.

    Args:
        query: The user's query
        context_chunks: Retrieved text chunks
        sources: Source information for citations

    Returns:
        Generated answer string
    """
    if not context_chunks:
        return "No relevant information found."

    # Build context with source references
    context_parts = []
    for i, (chunk, source) in enumerate(zip(context_chunks, sources), 1):
        context_parts.append(f"[Source {i}: {source['file']}]\n{chunk}")

    context = "\n\n---\n\n".join(context_parts)

    system_prompt = """You are a helpful assistant that answers questions based only on the provided context.

Instructions:
- Answer the user's question using ONLY the information from the provided context
- Be concise and direct
- If the context doesn't contain enough information to answer, say so
- Cite sources by referencing them like [Source 1] or [Source 2] when using information from them
- Do not make up information that isn't in the context"""

    user_prompt = f"""Context:
{context}

---

Question: {query}

Answer:"""

    try:
        response = openai_client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
        )

        answer = response.choices[0].message.content.strip()
        logger.info(f"Generated answer using {LLM_MODEL}")
        return answer

    except Exception as e:
        logger.error(f"Error generating answer with LLM: {e}")
        # Fallback to simple extraction if LLM fails
        return context_chunks[0].strip() if context_chunks else "Error generating answer."


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
