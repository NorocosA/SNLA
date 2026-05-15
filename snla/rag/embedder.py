"""
Sentence-Transformers Embedding Adapter for SNLA RAG.

Uses all-MiniLM-L6-v2 (~80 MB) for English text embedding.
Produces 384-dimensional vectors suitable for ChromaDB storage.

Design:
    - Lazy-loaded singleton model to avoid reloading on every query.
    - Batch processing for efficient bulk indexing.
    - Fallback to CPU if CUDA is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default embedding model (small, fast, good quality for English)
DEFAULT_MODEL_NAME: str = "all-MiniLM-L6-v2"
EMBEDDING_DIM: int = 384

_model: Any = None
_model_name: str | None = None


def _get_model(model_name: str = DEFAULT_MODEL_NAME) -> Any:
    """Lazy-load and cache the sentence-transformers model."""
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model

    from sentence_transformers import SentenceTransformer

    logger.info("Loading embedding model: %s", model_name)
    _model = SentenceTransformer(model_name)
    _model_name = model_name
    logger.info("Model loaded. Dimension: %d", _model.get_sentence_embedding_dimension())
    return _model


def embed_texts(
    texts: list[str],
    model_name: str = DEFAULT_MODEL_NAME,
    batch_size: int = 32,
    show_progress: bool = True,
) -> list[list[float]]:
    """Embed a list of text strings into dense vectors.

    Args:
        texts: List of text strings to embed.
        model_name: Sentence-Transformers model name.
        batch_size: Batch size for encoding.
        show_progress: Show tqdm progress bar.

    Returns:
        List of 384-dimensional float vectors.
    """
    model = _get_model(model_name)
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        convert_to_numpy=True,
    )
    return embeddings.tolist()


def embed_single(text: str, model_name: str = DEFAULT_MODEL_NAME) -> list[float]:
    """Embed a single text string.

    Args:
        text: Text to embed.
        model_name: Model name.

    Returns:
        384-dimensional float vector.
    """
    return embed_texts([text], model_name=model_name, show_progress=False)[0]


def get_embedding_dim(model_name: str = DEFAULT_MODEL_NAME) -> int:
    """Get the embedding dimension for a model."""
    model = _get_model(model_name)
    return model.get_sentence_embedding_dimension()


__all__ = [
    "embed_texts",
    "embed_single",
    "get_embedding_dim",
    "DEFAULT_MODEL_NAME",
    "EMBEDDING_DIM",
]
