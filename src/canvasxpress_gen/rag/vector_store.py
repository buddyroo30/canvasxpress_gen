"""
Vector store implementation using Milvus for storing and retrieving embeddings.

This module provides functionality for managing vector databases, including
creating collections, inserting embeddings, and performing similarity searches.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import logging
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from pymilvus import MilvusClient, DataType
    MILVUS_AVAILABLE = True
except ImportError:
    MilvusClient = None
    DataType = None
    MILVUS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""
    db_path: str = "/root/.cache/canvasxpress_llm.db"
    collection_name: str = "few_shot_examples"
    dimension: int = 1024  # BGE-M3 embedding dimension
    metric_type: str = "COSINE"
    index_type: str = "IVF_FLAT"
    nlist: int = 128


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    id: str
    score: float
    metadata: Dict[str, Any]


class VectorStore:
    """
    Vector store implementation using Milvus for embedding storage and retrieval.
    
    This class provides methods for creating collections, inserting embeddings,
    and performing similarity searches for the RAG system.
    """
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        """
        Initialize the vector store.
        
        Args:
            config: Configuration for the vector store
            
        Raises:
            ImportError: If Milvus is not available
        """
        if not MILVUS_AVAILABLE:
            raise ImportError(
                "Milvus dependency is required. Install with: pip install pymilvus"
            )
        
        self.config = config or VectorStoreConfig()
        self._client = None
        
    def _get_client(self) -> MilvusClient:
        """Get or create Milvus client."""
        if self._client is None:
            try:
                # Ensure directory exists
                db_dir = os.path.dirname(self.config.db_path)
                if db_dir:
                    Path(db_dir).mkdir(parents=True, exist_ok=True)
                
                self._client = MilvusClient(self.config.db_path)
                logger.info(f"Connected to Milvus database: {self.config.db_path}")
            except Exception as e:
                logger.error(f"Failed to connect to Milvus: {e}")
                raise
        
        return self._client
    
    def create_collection(
        self, 
        collection_name: Optional[str] = None,
        dimension: Optional[int] = None,
        drop_existing: bool = False
    ) -> bool:
        """
        Create a new collection in the vector store.
        
        Args:
            collection_name: Name of the collection to create
            dimension: Dimension of the vectors
            drop_existing: Whether to drop existing collection
            
        Returns:
            True if collection was created successfully
            
        Raises:
            RuntimeError: If collection creation fails
        """
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        dimension = dimension or self.config.dimension
        
        try:
            # Check if collection exists
            if client.has_collection(collection_name):
                if drop_existing:
                    client.drop_collection(collection_name)
                    logger.info(f"Dropped existing collection: {collection_name}")
                else:
                    logger.info(f"Collection already exists: {collection_name}")
                    return True
            
            # Create collection
            client.create_collection(
                collection_name=collection_name,
                dimension=dimension,
                metric_type=self.config.metric_type,
                consistency_level="Strong"
            )
            
            logger.info(f"Created collection: {collection_name} (dim={dimension})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            raise RuntimeError(f"Collection creation failed: {e}")
    
    def insert_embeddings(
        self,
        embeddings: List[List[float]],
        metadata: List[Dict[str, Any]],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        Insert embeddings with metadata into the collection.
        
        Args:
            embeddings: List of embedding vectors
            metadata: List of metadata dictionaries
            collection_name: Name of the collection
            
        Returns:
            List of inserted record IDs
            
        Raises:
            ValueError: If embeddings and metadata lengths don't match
            RuntimeError: If insertion fails
        """
        if len(embeddings) != len(metadata):
            raise ValueError("Embeddings and metadata must have same length")
        
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        
        try:
            # Prepare data for insertion
            data = []
            for i, (embedding, meta) in enumerate(zip(embeddings, metadata)):
                record = {
                    "id": meta.get("id", f"doc_{i}"),
                    "vector": embedding,
                    **meta
                }
                data.append(record)
            
            # Insert data
            result = client.insert(
                collection_name=collection_name,
                data=data
            )
            
            logger.info(f"Inserted {len(data)} records into {collection_name}")
            return result.get("ids", [])
            
        except Exception as e:
            logger.error(f"Failed to insert embeddings: {e}")
            raise RuntimeError(f"Embedding insertion failed: {e}")
    
    def search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        collection_name: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
        filter_expr: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search for similar embeddings in the collection.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            collection_name: Name of the collection to search
            output_fields: Fields to include in results
            filter_expr: Filter expression for search
            
        Returns:
            List of search results
            
        Raises:
            RuntimeError: If search fails
        """
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        
        try:
            # Perform search
            results = client.search(
                collection_name=collection_name,
                data=[query_embedding],
                limit=limit,
                output_fields=output_fields or ["*"],
                filter=filter_expr
            )
            
            # Convert results to SearchResult objects
            search_results = []
            if results and len(results) > 0:
                for hit in results[0]:  # First query results
                    search_result = SearchResult(
                        id=hit.get("id", ""),
                        score=hit.get("distance", 0.0),
                        metadata=hit.get("entity", {})
                    )
                    search_results.append(search_result)
            
            logger.debug(f"Found {len(search_results)} similar results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise RuntimeError(f"Vector search failed: {e}")
    
    def batch_search(
        self,
        query_embeddings: List[List[float]],
        limit: int = 10,
        collection_name: Optional[str] = None,
        output_fields: Optional[List[str]] = None
    ) -> List[List[SearchResult]]:
        """
        Perform batch search for multiple query embeddings.
        
        Args:
            query_embeddings: List of query embedding vectors
            limit: Maximum number of results per query
            collection_name: Name of the collection to search
            output_fields: Fields to include in results
            
        Returns:
            List of search results for each query
        """
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        
        try:
            results = client.search(
                collection_name=collection_name,
                data=query_embeddings,
                limit=limit,
                output_fields=output_fields or ["*"]
            )
            
            # Convert results
            all_results = []
            for query_results in results:
                search_results = []
                for hit in query_results:
                    search_result = SearchResult(
                        id=hit.get("id", ""),
                        score=hit.get("distance", 0.0),
                        metadata=hit.get("entity", {})
                    )
                    search_results.append(search_result)
                all_results.append(search_results)
            
            return all_results
            
        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            raise RuntimeError(f"Batch vector search failed: {e}")
    
    def delete_by_ids(
        self,
        ids: List[str],
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Delete records by their IDs.
        
        Args:
            ids: List of record IDs to delete
            collection_name: Name of the collection
            
        Returns:
            True if deletion was successful
        """
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        
        try:
            client.delete(
                collection_name=collection_name,
                ids=ids
            )
            logger.info(f"Deleted {len(ids)} records from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete records: {e}")
            return False
    
    def get_collection_stats(
        self, 
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary containing collection statistics
        """
        client = self._get_client()
        collection_name = collection_name or self.config.collection_name
        
        try:
            stats = client.get_collection_stats(collection_name)
            return {
                "collection_name": collection_name,
                "row_count": stats.get("row_count", 0),
                "data_size": stats.get("data_size", 0),
                "index_size": stats.get("index_size", 0)
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"collection_name": collection_name, "error": str(e)}
    
    def list_collections(self) -> List[str]:
        """
        List all collections in the database.
        
        Returns:
            List of collection names
        """
        client = self._get_client()
        
        try:
            collections = client.list_collections()
            return collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def close(self) -> None:
        """Close the database connection."""
        if self._client:
            try:
                self._client.close()
                self._client = None
                logger.info("Closed Milvus connection")
            except Exception as e:
                logger.error(f"Error closing Milvus connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation of the vector store."""
        return f"VectorStore(db_path={self.config.db_path}, collection={self.config.collection_name})"