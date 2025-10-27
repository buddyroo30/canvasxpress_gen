"""
RAG (Retrieval Augmented Generation) module for CanvasXpress Generation System.

This module provides vector database operations, embedding services, and retrieval
functionality for enhancing LLM responses with relevant context from CanvasXpress
documentation and few-shot examples.
"""

from .embedding_service import EmbeddingService, EmbeddingConfig
from .vector_store import VectorStore, VectorStoreConfig, SearchResult
from .retrieval_service import RetrievalService, RetrievalConfig
from .schema_processor import SchemaProcessor, SchemaField, FewShotExample

__all__ = [
    'EmbeddingService',
    'EmbeddingConfig',
    'VectorStore',
    'VectorStoreConfig',
    'SearchResult',
    'RetrievalService',
    'RetrievalConfig',
    'SchemaProcessor',
    'SchemaField',
    'FewShotExample'
]