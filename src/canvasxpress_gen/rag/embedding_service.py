"""
Embedding service for generating vector embeddings using BGE-M3 model.

This module provides functionality for encoding text into dense vector representations
for semantic similarity search in the RAG system.
"""

from typing import List, Dict, Any, Optional, Union
import logging
from dataclasses import dataclass
import numpy as np

try:
    from pymilvus.model.hybrid import BGEM3EmbeddingFunction
    from FlagEmbedding import BGEM3FlagModel
    MILVUS_AVAILABLE = True
except ImportError:
    BGEM3EmbeddingFunction = None
    BGEM3FlagModel = None
    MILVUS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding service."""
    model_name: str = 'BAAI/bge-m3'
    device: str = 'cpu'
    use_fp16: bool = False
    max_length: int = 8192
    batch_size: int = 32


class EmbeddingService:
    """
    Service for generating embeddings using BGE-M3 model.
    
    This service provides methods for encoding queries and documents into
    dense vector representations for semantic similarity search.
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize the embedding service.
        
        Args:
            config: Configuration for the embedding service
            
        Raises:
            ImportError: If required dependencies are not installed
        """
        if not MILVUS_AVAILABLE:
            raise ImportError(
                "Milvus and FlagEmbedding dependencies are required. "
                "Install with: pip install pymilvus FlagEmbedding"
            )
        
        self.config = config or EmbeddingConfig()
        self._embedding_function = None
        self._model = None
        
    def _initialize_embedding_function(self) -> None:
        """Initialize the BGE-M3 embedding function."""
        if self._embedding_function is None:
            try:
                self._embedding_function = BGEM3EmbeddingFunction(
                    model_name=self.config.model_name,
                    device=self.config.device,
                    use_fp16=self.config.use_fp16
                )
                logger.info(f"Initialized BGE-M3 embedding function with model: {self.config.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize embedding function: {e}")
                raise
    
    def _initialize_model(self) -> None:
        """Initialize the BGE-M3 model for direct usage."""
        if self._model is None:
            try:
                self._model = BGEM3FlagModel(
                    self.config.model_name,
                    device=self.config.device,
                    use_fp16=self.config.use_fp16
                )
                logger.info(f"Initialized BGE-M3 model: {self.config.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize BGE-M3 model: {e}")
                raise
    
    def encode_queries(self, queries: List[str]) -> Dict[str, List[List[float]]]:
        """
        Encode queries into embeddings.
        
        Args:
            queries: List of query strings to encode
            
        Returns:
            Dictionary containing dense embeddings for queries
            
        Raises:
            ValueError: If queries list is empty
            RuntimeError: If encoding fails
        """
        if not queries:
            raise ValueError("Queries list cannot be empty")
        
        self._initialize_embedding_function()
        
        try:
            embeddings = self._embedding_function.encode_queries(queries)
            logger.debug(f"Encoded {len(queries)} queries")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode queries: {e}")
            raise RuntimeError(f"Query encoding failed: {e}")
    
    def encode_documents(self, documents: List[str]) -> Dict[str, List[List[float]]]:
        """
        Encode documents into embeddings.
        
        Args:
            documents: List of document strings to encode
            
        Returns:
            Dictionary containing dense embeddings for documents
            
        Raises:
            ValueError: If documents list is empty
            RuntimeError: If encoding fails
        """
        if not documents:
            raise ValueError("Documents list cannot be empty")
        
        self._initialize_embedding_function()
        
        try:
            embeddings = self._embedding_function.encode_documents(documents)
            logger.debug(f"Encoded {len(documents)} documents")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to encode documents: {e}")
            raise RuntimeError(f"Document encoding failed: {e}")
    
    def encode_batch(
        self, 
        texts: List[str], 
        text_type: str = "query"
    ) -> List[List[float]]:
        """
        Encode a batch of texts with automatic batching.
        
        Args:
            texts: List of texts to encode
            text_type: Type of text ("query" or "document")
            
        Returns:
            List of dense embeddings
            
        Raises:
            ValueError: If invalid text_type or empty texts
        """
        if not texts:
            raise ValueError("Texts list cannot be empty")
        
        if text_type not in ["query", "document"]:
            raise ValueError("text_type must be 'query' or 'document'")
        
        # Process in batches to handle memory efficiently
        all_embeddings = []
        batch_size = self.config.batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            if text_type == "query":
                batch_embeddings = self.encode_queries(batch)["dense"]
            else:
                batch_embeddings = self.encode_documents(batch)["dense"]
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def compute_similarity(
        self, 
        query_embedding: List[float], 
        document_embeddings: List[List[float]]
    ) -> List[float]:
        """
        Compute cosine similarity between query and document embeddings.
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding vectors
            
        Returns:
            List of similarity scores
        """
        query_vec = np.array(query_embedding)
        doc_vecs = np.array(document_embeddings)
        
        # Normalize vectors
        query_norm = query_vec / np.linalg.norm(query_vec)
        doc_norms = doc_vecs / np.linalg.norm(doc_vecs, axis=1, keepdims=True)
        
        # Compute cosine similarity
        similarities = np.dot(doc_norms, query_norm)
        
        return similarities.tolist()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "model_name": self.config.model_name,
            "device": self.config.device,
            "use_fp16": self.config.use_fp16,
            "max_length": self.config.max_length,
            "batch_size": self.config.batch_size,
            "available": MILVUS_AVAILABLE
        }
    
    def __repr__(self) -> str:
        """String representation of the embedding service."""
        return f"EmbeddingService(model={self.config.model_name}, device={self.config.device})"