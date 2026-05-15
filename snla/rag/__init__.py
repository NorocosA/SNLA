"""
SNLA RAG Module — SPSS Command Syntax Knowledge Base.

Provides:
    - chunker:       PDF command extraction
    - embedder:      Sentence-transformers embedding
    - store:         ChromaDB vector storage
    - retriever:     High-level retrieval interface
    - integration:   SNLA module integrations (validator, syntax)
    - build_kb:      One-shot build script
"""

from snla.rag.retriever import Retriever, get_retriever

__all__ = ["Retriever", "get_retriever"]
