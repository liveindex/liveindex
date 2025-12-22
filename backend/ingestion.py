"""
Ingestion pipeline: Load → Chunk → Embed → Store

This module handles document ingestion into the vector database.
"""

import os
import hashlib
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_text_splitters import RecursiveCharacterTextSplitter

from embeddings import get_embeddings, EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)

# Qdrant configuration
COLLECTION_NAME = "documents"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# Supported file extensions
SUPPORTED_EXTENSIONS = {".md", ".txt", ".markdown"}


def get_qdrant_client() -> QdrantClient:
    """Get Qdrant client instance."""
    host = os.getenv("QDRANT_HOST", "localhost")
    port = int(os.getenv("QDRANT_PORT", "6333"))
    return QdrantClient(host=host, port=port)


def ensure_collection_exists(client: QdrantClient) -> None:
    """Create the documents collection if it doesn't exist."""
    try:
        client.get_collection(COLLECTION_NAME)
        logger.info(f"Collection '{COLLECTION_NAME}' already exists")
    except UnexpectedResponse:
        logger.info(f"Creating collection '{COLLECTION_NAME}'")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=EMBEDDING_DIMENSIONS,
                distance=models.Distance.COSINE,
            ),
        )


def load_document(file_path: str) -> str:
    """Load a document from disk."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str) -> List[str]:
    """Split text into chunks using RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def generate_chunk_id(file_path: str, chunk_index: int) -> str:
    """Generate a deterministic ID for a chunk based on file path and index."""
    content = f"{file_path}:{chunk_index}"
    return hashlib.md5(content.encode()).hexdigest()


async def ingest_file(
    file_path: str,
    client: Optional[QdrantClient] = None,
    base_dir: Optional[str] = None,
) -> Dict:
    """
    Ingest a single file into the vector database.

    Args:
        file_path: Path to the file to ingest
        client: Optional Qdrant client (creates one if not provided)
        base_dir: Base directory for relative path calculation

    Returns:
        dict with ingestion stats
    """
    start_time = time.time()

    if client is None:
        client = get_qdrant_client()
        ensure_collection_exists(client)

    # Load and chunk the document
    text = load_document(file_path)
    chunks = chunk_text(text)

    if not chunks:
        return {"chunks_created": 0, "time_seconds": 0.0}

    # Calculate relative path for storage
    if base_dir:
        relative_path = os.path.relpath(file_path, base_dir)
    else:
        relative_path = os.path.basename(file_path)

    # Get file modification time
    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()

    # Delete existing chunks for this file
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path",
                            match=models.MatchValue(value=relative_path),
                        )
                    ]
                )
            ),
        )
    except Exception as e:
        logger.debug(f"No existing chunks to delete for {relative_path}: {e}")

    # Get embeddings for all chunks (batched)
    embeddings = await get_embeddings(chunks)

    # Prepare points for Qdrant
    points = []
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        point_id = str(uuid4())
        points.append(
            models.PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "file_path": relative_path,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "updated_at": file_mtime,
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )
        )

    # Upsert points to Qdrant
    client.upsert(collection_name=COLLECTION_NAME, points=points)

    elapsed = time.time() - start_time
    logger.info(f"Ingested {relative_path}: {len(chunks)} chunks in {elapsed:.2f}s")

    return {
        "file": relative_path,
        "chunks_created": len(chunks),
        "time_seconds": elapsed,
    }


async def ingest_directory(directory: str) -> Dict:
    """
    Ingest all documents from a directory (recursively).

    Args:
        directory: Path to the directory containing documents

    Returns:
        dict with ingestion stats
    """
    start_time = time.time()

    client = get_qdrant_client()
    ensure_collection_exists(client)

    # Find all supported files
    directory_path = Path(directory)
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(directory_path.rglob(f"*{ext}"))

    if not files:
        logger.warning(f"No supported documents found in {directory}")
        return {
            "status": "success",
            "documents_ingested": 0,
            "chunks_created": 0,
            "time_seconds": 0.0,
        }

    logger.info(f"Found {len(files)} documents to ingest")

    total_chunks = 0
    documents_ingested = 0

    for file_path in files:
        try:
            result = await ingest_file(
                str(file_path),
                client=client,
                base_dir=directory,
            )
            total_chunks += result["chunks_created"]
            documents_ingested += 1
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")

    elapsed = time.time() - start_time
    logger.info(
        f"Ingestion complete: {documents_ingested} documents, "
        f"{total_chunks} chunks in {elapsed:.2f}s"
    )

    return {
        "status": "success",
        "documents_ingested": documents_ingested,
        "chunks_created": total_chunks,
        "time_seconds": elapsed,
    }


async def delete_file_chunks(file_path: str, base_dir: Optional[str] = None) -> int:
    """
    Delete all chunks for a specific file.

    Args:
        file_path: Path to the file
        base_dir: Base directory for relative path calculation

    Returns:
        Number of points deleted (approximate)
    """
    client = get_qdrant_client()

    if base_dir:
        relative_path = os.path.relpath(file_path, base_dir)
    else:
        relative_path = os.path.basename(file_path)

    try:
        result = client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="file_path",
                            match=models.MatchValue(value=relative_path),
                        )
                    ]
                )
            ),
        )
        logger.info(f"Deleted chunks for {relative_path}")
        return 1  # Qdrant doesn't return count, so we return 1 for success
    except Exception as e:
        logger.error(f"Failed to delete chunks for {relative_path}: {e}")
        return 0
