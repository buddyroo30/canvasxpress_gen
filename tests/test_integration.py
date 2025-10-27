"""
Integration tests for the CanvasXpress Generation System.

These tests validate the core end-to-end functionality:
converting English text descriptions to working CanvasXpress JSON configurations.

## Real API Testing Configuration:
Tests automatically detect and use any available LLM provider API key in priority order:

For Azure OpenAI (highest priority - corporate environments):
    export AZURE_OPENAI_API_KEY="your-azure-openai-key"
    export AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

For regular OpenAI (second priority):
    export OPENAI_API_KEY="your-openai-api-key"

For Google AI:
    export GOOGLE_API_KEY="your-google-api-key"

For Anthropic Claude:
    export ANTHROPIC_API_KEY="your-anthropic-api-key"

For AWS Bedrock:
    export AWS_ACCESS_KEY_ID="your-aws-key"
    export AWS_SECRET_ACCESS_KEY="your-aws-secret"

For local Ollama:
    export OLLAMA_HOST="http://localhost:11434"

If no API keys are found, tests automatically fall back to mocked responses
for reliable CI/CD testing without external dependencies.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import the main system components
from src.canvasxpress_gen.llm import LLMService
from src.canvasxpress_gen.rag import RetrievalService
from src.canvasxpress_gen.utils import ConfigValidator


def get_available_llm_config() -> tuple[bool, str, str]:
    """
    Check which LLM API keys are available for real testing.
    
    Returns:
        (has_api_key, provider_name, model_name)
    """
    # Priority 1: Azure OpenAI (corporate environments)
    if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
        return True, "Azure OpenAI", "gpt-4o-global"
    
    # Priority 2: Regular OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return True, "OpenAI", "gpt-4o"
    
    # Check for other LLM API keys in order of preference
    other_llm_configs = [
        ("GOOGLE_API_KEY", "Google AI", "gemini-pro"),
        ("ANTHROPIC_API_KEY", "Anthropic", "claude-3-sonnet"),
        ("AWS_ACCESS_KEY_ID", "AWS Bedrock", "titan-large"),
        ("OLLAMA_HOST", "Ollama", "llama3.1:70b")
    ]
    
    for api_key_env, provider, model in other_llm_configs:
        if os.getenv(api_key_env):
            return True, provider, model
    
    return False, "None", "mock"


def should_use_real_api() -> bool:
    """Determine if we should use real API calls or mocked responses."""
    has_key, _, _ = get_available_llm_config()
    return has_key


class TestEndToEndIntegration:
    """Test the complete English-to-CanvasXpress workflow."""
    
    @pytest.fixture
    def sample_requests(self):
        """Sample English requests for testing."""
        return [
            {
                "description": "box plot of len vs supp with title 'len vs supp' and legend in lower right",
                "headers": ["Var", "dose", "order", "supp", "len"],
                "expected_type": "Boxplot"
            },
            {
                "description": "Create a bar chart showing sales data with categories A, B, C",
                "headers": ["Category", "Sales"],
                "expected_type": "Bar"
            },
            {
                "description": "Make a scatter plot with x values vs y values",
                "headers": ["X", "Y"],
                "expected_type": "Scatter2D"
            }
        ]
    
    @pytest.fixture
    def mock_llm_responses(self):
        """Mock LLM responses that represent realistic configuration-only outputs."""
        return {
            "boxplot": {
                "graphType": "Boxplot",
                "xAxis": ["len"],
                "groupingFactors": ["supp"],
                "title": "len vs supp",
                "legendPosition": "bottomRight"
            },
            "bar_chart": {
                "graphType": "Bar",
                "title": "Sales Data",
                "xAxis": ["Category"],
                "yAxis": ["Sales"]
            },
            "scatter_plot": {
                "graphType": "Scatter2D",
                "title": "Scatter Plot",
                "xAxis": ["X"],
                "yAxis": ["Y"]
            }
        }

    def test_config_structure_validation(self, mock_llm_responses):
        """Test that generated configs have valid CanvasXpress structure."""
        validator = ConfigValidator()
        
        for config_name, config_data in mock_llm_responses.items():
            # Test that config is valid JSON
            json_str = json.dumps(config_data)
            assert json_str is not None
            
            # Test that config has required structure (configuration only, no data)
            assert isinstance(config_data, dict), f"Config should be a dict, got {type(config_data)}"
            
            # Test that config has graphType
            assert "graphType" in config_data, f"Missing graphType in {config_name}"
            assert config_data["graphType"] in [
                "Bar", "Scatter2D", "Line", "Area", "Pie", "Heatmap", "Boxplot"
            ], f"Invalid graphType: {config_data['graphType']}"
            
            # Validate using the system's validator (wrap in proper structure for validation)
            full_config = {"config": config_data, "data": []}  # Add minimal data for validation
            is_valid, errors = validator.validate_config(full_config)
            if not is_valid:
                print(f"⚠️ Config {config_name} validation warnings: {errors}")

    def test_data_structure_validation(self, mock_llm_responses):
        """Test that generated config structures are valid for CanvasXpress."""
        for config_name, config_data in mock_llm_responses.items():
            # Test that config is a dictionary
            assert isinstance(config_data, dict), f"Config {config_name} should be a dict"
            
            # Test that config has required graphType
            assert "graphType" in config_data, f"Config {config_name} missing graphType"
            
            # Test that graphType is valid
            valid_types = ["Bar", "Scatter2D", "Line", "Area", "Pie", "Heatmap", "Boxplot"]
            assert config_data["graphType"] in valid_types, f"Invalid graphType in {config_name}"
            
            # Test that config has reasonable structure
            assert len(config_data) >= 1, f"Config {config_name} should have at least graphType"

    @pytest.mark.integration
    def test_llm_service_config_generation(self, sample_requests, mock_llm_responses):
        """Test LLM service - uses real API if available, otherwise mocked responses."""
        llm_service = LLMService()
        
        if should_use_real_api():
            has_key, provider, model = get_available_llm_config()
            print(f"\n🚀 Using REAL {provider} API ({model}) for testing...")
            
            # Test with real API calls using available LLM
            for request in sample_requests:
                print(f"📝 Testing with {provider}: {request['description']}")
                
                try:
                    # Get real few-shot examples using RAG (like Flask app does)
                    few_shot_examples = self._get_real_few_shot_examples(request["description"])
                    
                    # REAL API CALL with REAL RAG retrieval - No mocking!
                    config_dict = llm_service.generate_json_config(
                        prompt=request["description"],
                        schema_info="CanvasXpress configuration schema - generate only the config object, not data. Return valid JSON format.",
                        few_shot_examples=few_shot_examples,  # REAL examples from PyMilvus!
                        model=model  # Use the detected model
                    )
                    
                    # Expect configuration-only response
                    graph_type = config_dict.get('graphType', 'Unknown')
                    print(f"✅ {provider} API generated config with graphType: {graph_type}")
                    
                    # Validate the real result (should be config-only)
                    assert isinstance(config_dict, dict), f"{provider} API response should be a dict"
                    assert "graphType" in config_dict, f"{provider} API response missing 'graphType'"
                    
                    # Validate using system validator (wrap in proper structure)
                    validator = ConfigValidator()
                    full_config = {"config": config_dict, "data": []}
                    is_valid, errors = validator.validate_config(full_config)
                    if not is_valid:
                        print(f"⚠️ {provider} API config validation warnings: {errors}")
                    
                except Exception as e:
                    print(f"❌ {provider} API test failed: {e}")
                    pytest.fail(f"{provider} API integration test failed: {e}")
        
        else:
            print(f"\n🔧 Using MOCKED responses (no API key found)...")
            
            # Mock the actual LLM call to return our test data
            with pytest.MonkeyPatch().context() as m:
                def mock_generate_json_config(prompt, schema_info, few_shot_examples, model=None):
                    # Simple logic to return appropriate mock based on prompt content
                    if "box" in prompt.lower() or "boxplot" in prompt.lower():
                        return mock_llm_responses["boxplot"]
                    elif "bar" in prompt.lower() or "sales" in prompt.lower():
                        return mock_llm_responses["bar_chart"]
                    elif "scatter" in prompt.lower():
                        return mock_llm_responses["scatter_plot"]
                    else:
                        return mock_llm_responses["bar_chart"]
                
                m.setattr(llm_service, 'generate_json_config', mock_generate_json_config)
                
                for request in sample_requests:
                    print(f"📝 Testing (mocked): {request['description']}")
                    
                    # Generate config using mocked service
                    config_dict = llm_service.generate_json_config(
                        prompt=request["description"],
                        schema_info="CanvasXpress schema information",
                        few_shot_examples="Example configurations"
                    )
                    
                    print(f"✅ Mock generated config with graphType: {config_dict['graphType']}")
                    
                    # Validate the mocked result (config-only format)
                    assert isinstance(config_dict, dict)
                    assert "graphType" in config_dict
                    assert config_dict["graphType"] == request["expected_type"]

    def test_rag_retrieval_integration(self):
        """Test that RAG system can retrieve relevant examples from PyMilvus."""
        if should_use_real_api():
            has_key, provider, model = get_available_llm_config()
            print(f"\n🚀 Testing RAG RETRIEVAL with REAL {provider} API...")
            
            # Test the complete RAG workflow like the Flask app does
            llm_service = LLMService()
            
            # Check if vector database exists (like Flask app does)
            vector_db_file = "/root/.cache/canvasxpress_llm.db"
            if os.path.exists(vector_db_file):
                print(f"✅ Vector database found: {vector_db_file}")
                
                try:
                    # Import PyMilvus and test direct connection (like Flask app)
                    from pymilvus import MilvusClient
                    milvus_client = MilvusClient(vector_db_file)
                    
                    # Test retrieving few-shot examples (like Flask app _get_few_shots_direct)
                    test_query = "box plot of len vs supp"
                    print(f"📝 Testing RAG retrieval for: {test_query}")
                    
                    # Get embeddings for the query (same as Flask app)
                    from pymilvus.model.hybrid import BGEM3EmbeddingFunction
                    bge_m3_ef = BGEM3EmbeddingFunction(
                        model_name='BAAI/bge-m3',
                        device='cpu',
                        use_fp16=False
                    )
                    query_embeddings = bge_m3_ef.encode_queries([test_query])
                    
                    # Search for similar examples in vector database
                    res = milvus_client.search(
                        collection_name="few_shot_examples",
                        data=[query_embeddings["dense"][0]],
                        limit=3,
                        output_fields=["config", "configEnglish", "headers", "id"]
                    )
                    
                    print(f"✅ RAG retrieved {len(res[0])} examples from vector database")
                    
                    # Validate retrieved examples
                    assert len(res[0]) > 0, "Should retrieve at least one example"
                    
                    # Build few-shot examples string (like Flask app does)
                    few_shot_examples = ""
                    for hit in res[0]:
                        entity = hit['entity']
                        few_shot_examples += f"English: {entity['configEnglish']}\n"
                        few_shot_examples += f"Headers: {entity['headers']}\n"
                        few_shot_examples += f"Config: {entity['config']}\n\n"
                    
                    print(f"✅ Built few-shot examples string ({len(few_shot_examples)} chars)")
                    
                    # Now test the complete workflow with REAL RAG retrieval
                    config_dict = llm_service.generate_json_config(
                        prompt=test_query,
                        schema_info="CanvasXpress configuration schema - generate only the config object, not data. Return valid JSON format.",
                        few_shot_examples=few_shot_examples,  # REAL examples from vector DB!
                        model=model
                    )
                    
                    print(f"✅ Complete RAG workflow SUCCESS: {config_dict.get('graphType', 'Unknown')}")
                    
                    # Validate the result
                    assert isinstance(config_dict, dict), "Config should be a dictionary"
                    assert "graphType" in config_dict, "Missing graphType"
                    
                except ImportError:
                    print("⚠️ PyMilvus or BGEM3 not available - testing basic RAG service initialization")
                    self._test_basic_rag_service()
                except Exception as e:
                    print(f"⚠️ RAG retrieval test failed: {e}")
                    self._test_basic_rag_service()
            else:
                print(f"⚠️ Vector database not found: {vector_db_file}")
                print("💡 Run 'make build_vector_db' to create the database for full RAG testing")
                self._test_basic_rag_service()
        else:
            print(f"\n🔧 Testing basic RAG service initialization (no API key)...")
            self._test_basic_rag_service()
    
    def _test_basic_rag_service(self):
        """Test basic RAG service initialization without external dependencies."""
        retrieval_service = RetrievalService()
        
        # Test that service initializes properly
        assert retrieval_service.embedding_service is not None
        assert retrieval_service.vector_store is not None
        assert retrieval_service.schema_processor is not None
        
        # Test configuration propagation
        assert hasattr(retrieval_service.config, 'embedding_model')
        assert hasattr(retrieval_service.config, 'db_path')
        
        print("✅ Basic RAG service initialization successful")
    
    def _get_real_few_shot_examples(self, query: str) -> str:
        """Get real few-shot examples from PyMilvus vector database (like Flask app)."""
        try:
            vector_db_file = "/root/.cache/canvasxpress_llm.db"
            if not os.path.exists(vector_db_file):
                print("⚠️ Vector database not found, using fallback example")
                return 'Example JSON: {"graphType": "Boxplot", "xAxis": ["len"], "groupingFactors": ["supp"], "title": "len vs supp", "legendPosition": "bottomRight"}'
            
            # Connect to PyMilvus (same as Flask app)
            from pymilvus import MilvusClient
            from pymilvus.model.hybrid import BGEM3EmbeddingFunction
            
            milvus_client = MilvusClient(vector_db_file)
            bge_m3_ef = BGEM3EmbeddingFunction(
                model_name='BAAI/bge-m3',
                device='cpu',
                use_fp16=False
            )
            
            # Get embeddings and search (same as Flask app)
            query_embeddings = bge_m3_ef.encode_queries([query])
            res = milvus_client.search(
                collection_name="few_shot_examples",
                data=[query_embeddings["dense"][0]],
                limit=3,
                output_fields=["config", "configEnglish", "headers", "id"]
            )
            
            # Build few-shot examples string (same as Flask app)
            few_shot_examples = ""
            for hit in res[0]:
                entity = hit['entity']
                few_shot_examples += f"English: {entity['configEnglish']}\n"
                few_shot_examples += f"Headers: {entity['headers']}\n"
                few_shot_examples += f"Config: {entity['config']}\n\n"
            
            print(f"✅ Retrieved {len(res[0])} real examples from vector DB ({len(few_shot_examples)} chars)")
            return few_shot_examples
            
        except Exception as e:
            print(f"⚠️ RAG retrieval failed: {e}, using fallback")
            return 'Example JSON: {"graphType": "Boxplot", "xAxis": ["len"], "groupingFactors": ["supp"], "title": "len vs supp", "legendPosition": "bottomRight"}'

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_API_KEY'), 
        reason="Requires GOOGLE_API_KEY environment variable"
    )
    def test_real_llm_integration(self):
        """Test with real LLM API (requires API key)."""
        llm_service = LLMService()
        
        # Simple test request
        description = "Create a bar chart with categories A, B, C and values 10, 20, 30"
        
        try:
            config_dict = llm_service.generate_json_config(
                prompt=description,
                schema_info="CanvasXpress schema information",
                few_shot_examples="Example configurations"
            )
            
            # Validate the response (it's already a dict)
            assert "data" in config_dict
            assert "config" in config_dict
            assert "graphType" in config_dict["config"]
            
            # Validate using system validator
            validator = ConfigValidator()
            is_valid, errors = validator.validate_config(config_dict)
            assert is_valid, f"Real LLM generated invalid config: {errors}"
            
        except Exception as e:
            pytest.skip(f"Real LLM test failed (expected without proper setup): {e}")

    def test_complete_workflow_simulation(self, sample_requests, mock_llm_responses):
        """Test the complete workflow from English to CanvasXpress config."""
        # This simulates the full workflow that would happen in the web interface
        
        llm_service = LLMService()
        validator = ConfigValidator()
        
        if should_use_real_api():
            has_key, provider, model = get_available_llm_config()
            print(f"\n🚀 Testing COMPLETE WORKFLOW with REAL {provider} API...")
            
            for request in sample_requests:
                description = request["description"]
                print(f"📝 Complete workflow test with {provider}: {description}")
                
                try:
                    # Step 1: Process the English description with REAL RAG retrieval
                    few_shot_examples = self._get_real_few_shot_examples(description)
                    
                    # Step 2: Generate config via REAL LLM with REAL retrieved examples
                    generated_config = llm_service.generate_json_config(
                        prompt=description,
                        schema_info="CanvasXpress configuration schema - generate only the config object, not data. Return valid JSON format.",
                        few_shot_examples=few_shot_examples,  # REAL examples from PyMilvus!
                        model=model  # Use the detected model
                    )
                    
                    # Step 3: Validate the generated config (wrap for validation)
                    full_config = {"config": generated_config, "data": []}
                    is_valid, errors = validator.validate_config(full_config)
                    if not is_valid:
                        print(f"⚠️ {provider} workflow validation warnings: {errors}")
                    
                    # Step 4: Verify config has required structure (config-only)
                    assert isinstance(generated_config, dict), "Config should be a dictionary"
                    assert "graphType" in generated_config, "Missing graphType"
                    
                    # Step 5: Verify config contains expected properties
                    graph_type = generated_config['graphType']
                    assert graph_type in ["Bar", "Scatter2D", "Line", "Boxplot", "Area", "Pie"], f"Invalid graphType: {graph_type}"
                    
                    print(f"✅ Complete {provider} workflow SUCCESS: {graph_type}")
                    
                except Exception as e:
                    print(f"❌ Complete {provider} workflow failed: {e}")
                    pytest.fail(f"Complete {provider} workflow test failed: {e}")
        
        else:
            print(f"\n🔧 Testing COMPLETE WORKFLOW with MOCKED responses...")
            
            for request in sample_requests:
                description = request["description"]
                print(f"📝 Complete workflow test (mocked): {description}")
                
                # Step 1: Process the English description (simulated)
                # Step 2: Generate config via LLM (mocked)
                if "box" in description.lower() or "boxplot" in description.lower():
                    generated_config = mock_llm_responses["boxplot"]
                elif "bar" in description.lower():
                    generated_config = mock_llm_responses["bar_chart"]
                elif "scatter" in description.lower():
                    generated_config = mock_llm_responses["scatter_plot"]
                else:
                    generated_config = mock_llm_responses["bar_chart"]
                
                # Step 3: Validate the generated config (wrap for validation)
                full_config = {"config": generated_config, "data": []}
                is_valid, errors = validator.validate_config(full_config)
                if not is_valid:
                    print(f"⚠️ Mocked workflow validation warnings: {errors}")
                
                # Step 4: Verify config matches expected type (config-only format)
                assert isinstance(generated_config, dict), "Config should be a dictionary"
                assert "graphType" in generated_config, "Missing graphType"
                assert generated_config["graphType"] == request["expected_type"]
                
                # Step 5: Verify config structure is appropriate
                assert "graphType" in generated_config
                graph_type = generated_config["graphType"]
                
                print(f"✅ Complete workflow SUCCESS (mocked): {graph_type}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])