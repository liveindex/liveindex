"""
OpenAI Embeddings wrapper.

This module provides embedding functionality using OpenAI's API.
"""

import os
import logging
from typing import List

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a single text.

    Args:
        text: The text to embed

    Returns:
        List of floats representing the embedding
    """
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise


async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts (batched).

    Args:
        texts: List of texts to embed

    Returns:
        List of embeddings
    """
    if not texts:
        return []

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        # Return embeddings in the same order as input
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"Error getting embeddings: {e}")
        raise
