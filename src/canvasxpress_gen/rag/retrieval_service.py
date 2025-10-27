"""
Retrieval service for the RAG system.

This module provides the main interface for retrieval-augmented generation,
combining embedding services, vector stores, and schema processing to provide
relevant context for LLM queries.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import logging
from dataclasses import dataclass
from pathlib import Path

from .embedding_service import EmbeddingService, EmbeddingConfig
from .vector_store import VectorStore, VectorStoreConfig, SearchResult
from .schema_processor import SchemaProcessor, FewShotExample

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for the retrieval service."""
    # Vector store settings
    db_path: str = "/root/.cache/canvasxpress_llm.db"
    collection_name: str = "few_shot_examples"
    
    # Embedding settings
    embedding_model: str = 'BAAI/bge-m3'
    embedding_device: str = 'cpu'
    
    # Retrieval settings
    default_limit: int = 5
    similarity_threshold: float = 0.7
    
    # Data file paths
    docs_file: str = "doc.json"
    examples_file: str = "all_few_shots.json"


@dataclass
class RetrievalResult:
    """Result from retrieval operation."""
    query: str
    results: List[SearchResult]
    context: str
    metadata: Dict[str, Any]


class RetrievalService:
    """
    Main retrieval service for the RAG system.
    
    This service coordinates embedding generation, vector storage, and retrieval
    to provide relevant context for LLM queries about CanvasXpress configuration.
    """
    
    def __init__(self, config: Optional[RetrievalConfig] = None):
        """
        Initialize the retrieval service.
        
        Args:
            config: Configuration for the retrieval service
        """
        self.config = config or RetrievalConfig()
        
        # Initialize components
        self.embedding_service = EmbeddingService(
            EmbeddingConfig(
                model_name=self.config.embedding_model,
                device=self.config.embedding_device
            )
        )
        
        self.vector_store = VectorStore(
            VectorStoreConfig(
                db_path=self.config.db_path,
                collection_name=self.config.collection_name
            )
        )
        
        self.schema_processor = SchemaProcessor()
        
        # State
        self._initialized = False
    
    def initialize(
        self,
        docs_file: Optional[str] = None,
        examples_file: Optional[str] = None,
        force_rebuild: bool = False
    ) -> bool:
        """
        Initialize the retrieval service with data.
        
        Args:
            docs_file: Path to CanvasXpress documentation file
            examples_file: Path to few-shot examples file
            force_rebuild: Whether to force rebuild of vector database
            
        Returns:
            True if initialization was successful
            
        Raises:
            FileNotFoundError: If required files are not found
            RuntimeError: If initialization fails
        """
        docs_path = docs_file or self.config.docs_file
        examples_path = examples_file or self.config.examples_file
        
        try:
            # Load schema documentation
            if Path(docs_path).exists():
                self.schema_processor.load_canvasxpress_docs(docs_path)
                logger.info(f"Loaded schema documentation from {docs_path}")
            else:
                logger.warning(f"Documentation file not found: {docs_path}")
            
            # Load few-shot examples
            if Path(examples_path).exists():
                self.schema_processor.load_few_shot_examples(examples_path)
                logger.info(f"Loaded few-shot examples from {examples_path}")
            else:
                logger.warning(f"Examples file not found: {examples_path}")
            
            # Initialize vector database if needed
            if force_rebuild or not self._is_database_initialized():
                self._build_vector_database()
            
            self._initialized = True
            logger.info("Retrieval service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize retrieval service: {e}")
            raise RuntimeError(f"Initialization failed: {e}")
    
    def _is_database_initialized(self) -> bool:
        """Check if the vector database is already initialized."""
        try:
            collections = self.vector_store.list_collections()
            return self.config.collection_name in collections
        except Exception:
            return False
    
    def _build_vector_database(self) -> None:
        """Build the vector database from loaded data."""
        logger.info("Building vector database...")
        
        # Prepare data for vectorization
        texts, metadata = self.schema_processor.prepare_vectorization_data()
        
        if not texts:
            logger.warning("No data available for vectorization")
            return
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(texts)} items...")
        embeddings = self.embedding_service.encode_batch(texts, text_type="document")
        
        # Create collection
        self.vector_store.create_collection(drop_existing=True)
        
        # Insert embeddings
        self.vector_store.insert_embeddings(embeddings, metadata)
        
        logger.info(f"Vector database built with {len(embeddings)} embeddings")
    
    def retrieve(
        self,
        query: str,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        filter_type: Optional[str] = None
    ) -> RetrievalResult:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: Query string
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            filter_type: Filter results by type ("schema" or "example")
            
        Returns:
            RetrievalResult containing query results and formatted context
            
        Raises:
            RuntimeError: If retrieval fails
        """
        if not self._initialized:
            raise RuntimeError("Retrieval service not initialized. Call initialize() first.")
        
        limit = limit or self.config.default_limit
        threshold = similarity_threshold or self.config.similarity_threshold
        
        try:
            # Generate query embedding
            query_embeddings = self.embedding_service.encode_queries([query])
            query_embedding = query_embeddings["dense"][0]
            
            # Build filter expression
            filter_expr = None
            if filter_type:
                filter_expr = f'type == "{filter_type}"'
            
            # Search vector database
            search_results = self.vector_store.search(
                query_embedding=query_embedding,
                limit=limit * 2,  # Get more results to filter by threshold
                filter_expr=filter_expr
            )
            
            # Filter by similarity threshold
            filtered_results = [
                result for result in search_results 
                if result.score >= threshold
            ][:limit]
            
            # Format context
            context = self._format_context(filtered_results)
            
            # Create retrieval result
            retrieval_result = RetrievalResult(
                query=query,
                results=filtered_results,
                context=context,
                metadata={
                    "total_results": len(search_results),
                    "filtered_results": len(filtered_results),
                    "similarity_threshold": threshold,
                    "filter_type": filter_type
                }
            )
            
            logger.debug(f"Retrieved {len(filtered_results)} results for query: {query[:50]}...")
            return retrieval_result
            
        except Exception as e:
            logger.error(f"Retrieval failed for query '{query}': {e}")
            raise RuntimeError(f"Retrieval failed: {e}")
    
    def retrieve_examples(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[FewShotExample]:
        """
        Retrieve few-shot examples relevant to a query.
        
        Args:
            query: Query string
            limit: Maximum number of examples to return
            
        Returns:
            List of relevant few-shot examples
        """
        retrieval_result = self.retrieve(
            query=query,
            limit=limit,
            filter_type="example"
        )
        
        examples = []
        for result in retrieval_result.results:
            if result.metadata.get("type") == "example":
                example = FewShotExample(
                    id=result.metadata.get("id", ""),
                    config_english=result.metadata.get("configEnglish", ""),
                    headers=result.metadata.get("headers", []),
                    config=result.metadata.get("config", {}),
                    metadata=result.metadata.get("metadata", {})
                )
                examples.append(example)
        
        return examples
    
    def retrieve_schema_info(
        self,
        query: str,
        limit: Optional[int] = None
    ) -> List[str]:
        """
        Retrieve schema information relevant to a query.
        
        Args:
            query: Query string
            limit: Maximum number of schema records to return
            
        Returns:
            List of relevant schema information strings
        """
        retrieval_result = self.retrieve(
            query=query,
            limit=limit,
            filter_type="schema"
        )
        
        schema_info = []
        for result in retrieval_result.results:
            if result.metadata.get("type") == "schema":
                content = result.metadata.get("content", "")
                if content:
                    schema_info.append(content)
        
        return schema_info
    
    def _format_context(self, results: List[SearchResult]) -> str:
        """
        Format search results into context string for LLM.
        
        Args:
            results: List of search results
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant context found."
        
        context_parts = []
        
        # Group results by type
        examples = []
        schema_info = []
        
        for result in results:
            if result.metadata.get("type") == "example":
                examples.append(result)
            elif result.metadata.get("type") == "schema":
                schema_info.append(result)
        
        # Add schema information
        if schema_info:
            context_parts.append("## Relevant Schema Information:")
            for i, result in enumerate(schema_info, 1):
                content = result.metadata.get("content", "")
                context_parts.append(f"{i}. {content}")
            context_parts.append("")
        
        # Add few-shot examples
        if examples:
            context_parts.append("## Relevant Examples:")
            for i, result in enumerate(examples, 1):
                english = result.metadata.get("configEnglish", "")
                config = result.metadata.get("config", {})
                
                context_parts.append(f"{i}. Description: {english}")
                if config:
                    context_parts.append(f"   Configuration: {config}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def batch_retrieve(
        self,
        queries: List[str],
        limit: Optional[int] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve context for multiple queries.
        
        Args:
            queries: List of query strings
            limit: Maximum number of results per query
            
        Returns:
            List of retrieval results
        """
        results = []
        for query in queries:
            try:
                result = self.retrieve(query, limit=limit)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to retrieve for query '{query}': {e}")
                # Add empty result for failed queries
                results.append(RetrievalResult(
                    query=query,
                    results=[],
                    context="",
                    metadata={"error": str(e)}
                ))
        
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database.
        
        Returns:
            Dictionary containing database statistics
        """
        try:
            stats = self.vector_store.get_collection_stats()
            processor_stats = self.schema_processor.get_stats()
            
            return {
                "vector_store": stats,
                "schema_processor": processor_stats,
                "embedding_service": self.embedding_service.get_model_info(),
                "initialized": self._initialized
            }
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
    
    def rebuild_database(
        self,
        docs_file: Optional[str] = None,
        examples_file: Optional[str] = None
    ) -> bool:
        """
        Rebuild the vector database with fresh data.
        
        Args:
            docs_file: Path to documentation file
            examples_file: Path to examples file
            
        Returns:
            True if rebuild was successful
        """
        try:
            logger.info("Rebuilding vector database...")
            return self.initialize(
                docs_file=docs_file,
                examples_file=examples_file,
                force_rebuild=True
            )
        except Exception as e:
            logger.error(f"Failed to rebuild database: {e}")
            return False
    
    def close(self) -> None:
        """Close the retrieval service and cleanup resources."""
        try:
            self.vector_store.close()
            logger.info("Retrieval service closed")
        except Exception as e:
            logger.error(f"Error closing retrieval service: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def __repr__(self) -> str:
        """String representation of the retrieval service."""
        return f"RetrievalService(initialized={self._initialized}, db={self.config.db_path})"