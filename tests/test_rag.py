"""
Tests for the RAG (Retrieval Augmented Generation) module.

This module contains comprehensive tests for all RAG components including
embedding services, vector stores, schema processing, and retrieval services.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import RAG components
from src.canvasxpress_gen.rag import (
    EmbeddingService, EmbeddingConfig,
    VectorStore, VectorStoreConfig, SearchResult,
    SchemaProcessor, SchemaField, FewShotExample,
    RetrievalService, RetrievalConfig
)


class TestEmbeddingService:
    """Tests for the EmbeddingService class."""
    
    def test_embedding_config_creation(self):
        """Test EmbeddingConfig creation and defaults."""
        config = EmbeddingConfig()
        assert config.model_name == 'BAAI/bge-m3'
        assert config.device == 'cpu'
        assert config.use_fp16 is False
        assert config.max_length == 8192
        assert config.batch_size == 32
    
    def test_embedding_config_custom(self):
        """Test EmbeddingConfig with custom values."""
        config = EmbeddingConfig(
            model_name='custom-model',
            device='cuda',
            use_fp16=True,
            batch_size=16
        )
        assert config.model_name == 'custom-model'
        assert config.device == 'cuda'
        assert config.use_fp16 is True
        assert config.batch_size == 16
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', False)
    def test_embedding_service_import_error(self):
        """Test EmbeddingService raises ImportError when dependencies missing."""
        with pytest.raises(ImportError, match="Milvus and FlagEmbedding dependencies are required"):
            EmbeddingService()
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.embedding_service.BGEM3EmbeddingFunction')
    def test_embedding_service_initialization(self, mock_embedding_func):
        """Test EmbeddingService initialization."""
        service = EmbeddingService()
        assert service.config.model_name == 'BAAI/bge-m3'
        assert service._embedding_function is None
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.embedding_service.BGEM3EmbeddingFunction')
    def test_encode_queries(self, mock_embedding_func):
        """Test query encoding."""
        # Setup mock
        mock_func_instance = Mock()
        mock_func_instance.encode_queries.return_value = {
            "dense": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        }
        mock_embedding_func.return_value = mock_func_instance
        
        service = EmbeddingService()
        queries = ["test query 1", "test query 2"]
        
        result = service.encode_queries(queries)
        
        assert "dense" in result
        assert len(result["dense"]) == 2
        mock_func_instance.encode_queries.assert_called_once_with(queries)
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.embedding_service.BGEM3EmbeddingFunction')
    def test_encode_queries_empty_list(self, mock_embedding_func):
        """Test encoding empty queries list raises ValueError."""
        service = EmbeddingService()
        
        with pytest.raises(ValueError, match="Queries list cannot be empty"):
            service.encode_queries([])
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.embedding_service.BGEM3EmbeddingFunction')
    def test_encode_documents(self, mock_embedding_func):
        """Test document encoding."""
        # Setup mock
        mock_func_instance = Mock()
        mock_func_instance.encode_documents.return_value = {
            "dense": [[0.7, 0.8, 0.9]]
        }
        mock_embedding_func.return_value = mock_func_instance
        
        service = EmbeddingService()
        documents = ["test document"]
        
        result = service.encode_documents(documents)
        
        assert "dense" in result
        assert len(result["dense"]) == 1
        mock_func_instance.encode_documents.assert_called_once_with(documents)
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    def test_get_model_info(self):
        """Test getting model information."""
        config = EmbeddingConfig(model_name='test-model', device='cuda')
        service = EmbeddingService(config)
        
        info = service.get_model_info()
        
        assert info["model_name"] == 'test-model'
        assert info["device"] == 'cuda'
        assert info["available"] is True


class TestVectorStore:
    """Tests for the VectorStore class."""
    
    def test_vector_store_config_creation(self):
        """Test VectorStoreConfig creation and defaults."""
        config = VectorStoreConfig()
        assert config.db_path == "/root/.cache/canvasxpress_llm.db"
        assert config.collection_name == "few_shot_examples"
        assert config.dimension == 1024
        assert config.metric_type == "COSINE"
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', False)
    def test_vector_store_import_error(self):
        """Test VectorStore raises ImportError when Milvus not available."""
        with pytest.raises(ImportError, match="Milvus dependency is required"):
            VectorStore()
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MilvusClient')
    def test_vector_store_initialization(self, mock_client):
        """Test VectorStore initialization."""
        store = VectorStore()
        assert store.config.collection_name == "few_shot_examples"
        assert store._client is None
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MilvusClient')
    @patch('src.canvasxpress_gen.rag.vector_store.Path')
    def test_get_client(self, mock_path, mock_client):
        """Test client creation."""
        mock_path.return_value.mkdir = Mock()
        mock_client_instance = Mock()
        mock_client.return_value = mock_client_instance
        
        store = VectorStore()
        client = store._get_client()
        
        assert client == mock_client_instance
        mock_client.assert_called_once_with(store.config.db_path)
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MilvusClient')
    def test_create_collection(self, mock_client):
        """Test collection creation."""
        mock_client_instance = Mock()
        mock_client_instance.has_collection.return_value = False
        mock_client.return_value = mock_client_instance
        
        store = VectorStore()
        result = store.create_collection()
        
        assert result is True
        mock_client_instance.create_collection.assert_called_once()
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MilvusClient')
    def test_insert_embeddings(self, mock_client):
        """Test embedding insertion."""
        mock_client_instance = Mock()
        mock_client_instance.insert.return_value = {"ids": ["1", "2"]}
        mock_client.return_value = mock_client_instance
        
        store = VectorStore()
        embeddings = [[0.1, 0.2], [0.3, 0.4]]
        metadata = [{"id": "1", "text": "doc1"}, {"id": "2", "text": "doc2"}]
        
        result = store.insert_embeddings(embeddings, metadata)
        
        assert result == ["1", "2"]
        mock_client_instance.insert.assert_called_once()
    
    def test_insert_embeddings_length_mismatch(self):
        """Test insertion with mismatched lengths raises ValueError."""
        with patch('canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True):
            store = VectorStore()
            embeddings = [[0.1, 0.2]]
            metadata = [{"id": "1"}, {"id": "2"}]
            
            with pytest.raises(ValueError, match="Embeddings and metadata must have same length"):
                store.insert_embeddings(embeddings, metadata)
    
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MilvusClient')
    def test_search(self, mock_client):
        """Test vector search."""
        mock_client_instance = Mock()
        mock_client_instance.search.return_value = [[
            {"id": "1", "distance": 0.9, "entity": {"text": "result1"}},
            {"id": "2", "distance": 0.8, "entity": {"text": "result2"}}
        ]]
        mock_client.return_value = mock_client_instance
        
        store = VectorStore()
        query_embedding = [0.1, 0.2, 0.3]
        
        results = store.search(query_embedding, limit=2)
        
        assert len(results) == 2
        assert results[0].id == "1"
        assert results[0].score == 0.9
        assert results[1].id == "2"
        assert results[1].score == 0.8


class TestSchemaProcessor:
    """Tests for the SchemaProcessor class."""
    
    def test_schema_field_creation(self):
        """Test SchemaField creation."""
        field = SchemaField(
            name="testField",
            description="Test description",
            field_type="string",
            category="general",
            options=["option1", "option2"],
            default_value="default"
        )
        
        assert field.name == "testField"
        assert field.description == "Test description"
        assert field.field_type == "string"
        assert field.category == "general"
        assert field.options == ["option1", "option2"]
        assert field.default_value == "default"
    
    def test_few_shot_example_creation(self):
        """Test FewShotExample creation."""
        example = FewShotExample(
            id="test_1",
            config_english="Create a bar chart",
            headers=["x", "y"],
            config={"graphType": "Bar"},
            metadata={"source": "test"}
        )
        
        assert example.id == "test_1"
        assert example.config_english == "Create a bar chart"
        assert example.headers == ["x", "y"]
        assert example.config == {"graphType": "Bar"}
        assert example.metadata == {"source": "test"}
    
    def test_schema_processor_initialization(self):
        """Test SchemaProcessor initialization."""
        processor = SchemaProcessor()
        assert len(processor.schema_fields) == 0
        assert len(processor.few_shot_examples) == 0
    
    def test_load_canvasxpress_docs_file_not_found(self):
        """Test loading docs with non-existent file."""
        processor = SchemaProcessor()
        
        with pytest.raises(FileNotFoundError):
            processor.load_canvasxpress_docs("nonexistent.json")
    
    def test_load_canvasxpress_docs_success(self):
        """Test successful documentation loading."""
        # Create temporary docs file
        docs_data = {
            "P": {
                "graphType": {
                    "C": "Type of graph to create<br>",
                    "T": "string",
                    "M": "general",
                    "O": ["Bar", "Line", "Scatter"],
                    "D": "Bar"
                },
                "title": {
                    "C": "Title of the graph",
                    "T": "string"
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(docs_data, f)
            temp_file = f.name
        
        try:
            processor = SchemaProcessor()
            fields = processor.load_canvasxpress_docs(temp_file)
            
            assert len(fields) == 2
            assert "graphType" in fields
            assert "title" in fields
            
            graph_type_field = fields["graphType"]
            assert graph_type_field.name == "graphType"
            assert graph_type_field.description == "Type of graph to create"  # <br> stripped
            assert graph_type_field.field_type == "string"
            assert graph_type_field.category == "general"
            assert graph_type_field.options == ["Bar", "Line", "Scatter"]
            assert graph_type_field.default_value == "Bar"
            
        finally:
            os.unlink(temp_file)
    
    def test_generate_schema_records(self):
        """Test schema record generation."""
        processor = SchemaProcessor()
        
        # Add test fields
        processor.schema_fields = {
            "graphType": SchemaField(
                name="graphType",
                description="Type of graph",
                field_type="string",
                options=["Bar", "Line"]
            ),
            "title": SchemaField(
                name="title",
                description="Graph title",
                field_type="string"
            )
        }
        
        records = processor.generate_schema_records()
        
        assert len(records) == 2
        assert any("graphType:" in record for record in records)
        assert any("title:" in record for record in records)
        assert any("Type of graph" in record for record in records)
        assert any("Options for Field Value: [Bar,Line]" in record for record in records)
    
    def test_load_few_shot_examples_success(self):
        """Test successful few-shot examples loading."""
        examples_data = [
            {
                "id": "example_1",
                "configEnglish": "Create a bar chart",
                "headers": ["x", "y"],
                "config": {
                    "graphType": "Bar",
                    "showLegend": "true"
                }
            },
            {
                "id": "example_2",
                "configEnglish": "Create a line chart",
                "headers": ["time", "value"],
                "config": {
                    "graphType": "Line",
                    "showLegend": "false"
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(examples_data, f)
            temp_file = f.name
        
        try:
            processor = SchemaProcessor()
            examples = processor.load_few_shot_examples(temp_file)
            
            assert len(examples) == 2
            
            # Check first example
            example1 = examples[0]
            assert example1.id == "example_1"
            assert example1.config_english == "Create a bar chart"
            assert example1.headers == ["x", "y"]
            assert example1.config["graphType"] == "Bar"
            assert example1.config["showLegend"] is True  # Converted from string
            
            # Check second example
            example2 = examples[1]
            assert example2.config["showLegend"] is False  # Converted from string
            
        finally:
            os.unlink(temp_file)
    
    def test_convert_boolean_dict_values(self):
        """Test boolean conversion in nested dictionaries."""
        processor = SchemaProcessor()
        
        test_data = {
            "bool_true": "true",
            "bool_false": "false",
            "string": "normal_string",
            "nested": {
                "inner_true": "true",
                "inner_false": "false"
            },
            "list": ["true", "false", "normal"]
        }
        
        result = processor._convert_boolean_dict_values(test_data)
        
        assert result["bool_true"] is True
        assert result["bool_false"] is False
        assert result["string"] == "normal_string"
        assert result["nested"]["inner_true"] is True
        assert result["nested"]["inner_false"] is False
        assert result["list"][0] is True
        assert result["list"][1] is False
        assert result["list"][2] == "normal"
    
    def test_prepare_vectorization_data(self):
        """Test preparation of data for vectorization."""
        processor = SchemaProcessor()
        
        # Add test schema fields
        processor.schema_fields = {
            "graphType": SchemaField(name="graphType", description="Graph type")
        }
        
        # Add test examples
        processor.few_shot_examples = [
            FewShotExample(
                id="ex1",
                config_english="Create bar chart",
                headers=["x"],
                config={"graphType": "Bar"}
            )
        ]
        
        texts, metadata = processor.prepare_vectorization_data()
        
        assert len(texts) == 2  # 1 schema + 1 example
        assert len(metadata) == 2
        
        # Check schema record
        schema_meta = next(m for m in metadata if m["type"] == "schema")
        assert "graphType:" in schema_meta["content"]
        
        # Check example record
        example_meta = next(m for m in metadata if m["type"] == "example")
        assert example_meta["configEnglish"] == "Create bar chart"
        assert example_meta["config"] == {"graphType": "Bar"}
    
    def test_get_stats(self):
        """Test getting processor statistics."""
        processor = SchemaProcessor()
        
        # Add test data
        processor.schema_fields = {"field1": SchemaField(name="field1")}
        processor.few_shot_examples = [
            FewShotExample(id="ex1", config_english="test", headers=[], config={})
        ]
        
        stats = processor.get_stats()
        
        assert stats["schema_fields_count"] == 1
        assert stats["few_shot_examples_count"] == 1
        assert "field1" in stats["schema_fields"]
        assert "ex1" in stats["example_ids"]


class TestRetrievalService:
    """Tests for the RetrievalService class."""
    
    def test_retrieval_config_creation(self):
        """Test RetrievalConfig creation and defaults."""
        config = RetrievalConfig()
        assert config.db_path == "/root/.cache/canvasxpress_llm.db"
        assert config.collection_name == "few_shot_examples"
        assert config.embedding_model == 'BAAI/bge-m3'
        assert config.default_limit == 5
        assert config.similarity_threshold == 0.7
    
    @patch('src.canvasxpress_gen.rag.retrieval_service.EmbeddingService')
    @patch('src.canvasxpress_gen.rag.retrieval_service.VectorStore')
    @patch('src.canvasxpress_gen.rag.retrieval_service.SchemaProcessor')
    def test_retrieval_service_initialization(self, mock_processor, mock_store, mock_embedding):
        """Test RetrievalService initialization."""
        service = RetrievalService()
        
        assert service._initialized is False
        mock_embedding.assert_called_once()
        mock_store.assert_called_once()
        mock_processor.assert_called_once()
    
    @patch('src.canvasxpress_gen.rag.retrieval_service.EmbeddingService')
    @patch('src.canvasxpress_gen.rag.retrieval_service.VectorStore')
    @patch('src.canvasxpress_gen.rag.retrieval_service.SchemaProcessor')
    def test_retrieve_not_initialized(self, mock_processor, mock_store, mock_embedding):
        """Test retrieve raises error when not initialized."""
        service = RetrievalService()
        
        with pytest.raises(RuntimeError, match="Retrieval service not initialized"):
            service.retrieve("test query")
    
    def test_repr_methods(self):
        """Test string representations of classes."""
        # Test EmbeddingService repr
        with patch('canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True):
            config = EmbeddingConfig(model_name='test-model', device='cuda')
            service = EmbeddingService(config)
            repr_str = repr(service)
            assert 'test-model' in repr_str
            assert 'cuda' in repr_str
        
        # Test VectorStore repr
        with patch('canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True):
            config = VectorStoreConfig(db_path='/test/path', collection_name='test_collection')
            store = VectorStore(config)
            repr_str = repr(store)
            assert '/test/path' in repr_str
            assert 'test_collection' in repr_str
        
        # Test SchemaProcessor repr
        processor = SchemaProcessor()
        processor.schema_fields = {"field1": SchemaField(name="field1")}
        processor.few_shot_examples = [
            FewShotExample(id="ex1", config_english="test", headers=[], config={})
        ]
        repr_str = repr(processor)
        assert 'fields=1' in repr_str
        assert 'examples=1' in repr_str


# Integration tests
@pytest.mark.integration
class TestRAGIntegration:
    """Integration tests for RAG components."""
    
    @patch('src.canvasxpress_gen.rag.embedding_service.MILVUS_AVAILABLE', True)
    @patch('src.canvasxpress_gen.rag.vector_store.MILVUS_AVAILABLE', True)
    def test_end_to_end_workflow(self):
        """Test end-to-end RAG workflow with mocked dependencies."""
        # This test would require actual Milvus and embedding models
        # For now, we'll test the component integration structure
        
        with patch('canvasxpress_gen.rag.embedding_service.BGEM3EmbeddingFunction'), \
             patch('canvasxpress_gen.rag.vector_store.MilvusClient'):
            
            # Create service
            service = RetrievalService()
            
            # Test that components are properly initialized
            assert service.embedding_service is not None
            assert service.vector_store is not None
            assert service.schema_processor is not None
            
            # Test configuration propagation
            assert service.embedding_service.config.model_name == service.config.embedding_model
            assert service.vector_store.config.db_path == service.config.db_path


if __name__ == "__main__":
    pytest.main([__file__])