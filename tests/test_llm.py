"""
Tests for LLM module functionality.
"""

import pytest
from unittest.mock import Mock, patch
import json

from src.canvasxpress_gen.llm import LLMService, ModelConfig, SupportedModels, ModelProvider


class TestModelConfig:
    """Test ModelConfig class."""
    
    def test_model_config_creation(self):
        """Test creating a ModelConfig instance."""
        config = ModelConfig(
            name="Test Model",
            provider=ModelProvider.GOOGLE,
            model_id="test-model",
            max_tokens=1024,
            temperature=0.5
        )
        
        assert config.name == "Test Model"
        assert config.provider == ModelProvider.GOOGLE
        assert config.model_id == "test-model"
        assert config.max_tokens == 1024
        assert config.temperature == 0.5
    
    def test_model_config_to_dict(self):
        """Test converting ModelConfig to dictionary."""
        config = ModelConfig(
            name="Test Model",
            provider=ModelProvider.GOOGLE,
            model_id="test-model"
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["name"] == "Test Model"
        assert config_dict["provider"] == "google"
        assert config_dict["model_id"] == "test-model"
    
    def test_model_config_from_dict(self):
        """Test creating ModelConfig from dictionary."""
        data = {
            "name": "Test Model",
            "provider": "google",
            "model_id": "test-model",
            "max_tokens": 2048
        }
        
        config = ModelConfig.from_dict(data)
        
        assert config.name == "Test Model"
        assert config.provider == ModelProvider.GOOGLE
        assert config.model_id == "test-model"
        assert config.max_tokens == 2048


class TestSupportedModels:
    """Test SupportedModels class."""
    
    def test_get_all_models(self):
        """Test getting all supported models."""
        models = SupportedModels.get_all_models()
        
        assert isinstance(models, dict)
        assert len(models) > 0
        assert "Gemini 1.5 Flash" in models
        assert "Claude 3.5 Sonnet" in models
    
    def test_get_model_by_name(self):
        """Test getting a model by name."""
        model = SupportedModels.get_model_by_name("Gemini 1.5 Flash")
        
        assert model is not None
        assert model.name == "Gemini 1.5 Flash"
        assert model.provider == ModelProvider.GOOGLE
    
    def test_get_model_by_name_not_found(self):
        """Test getting a non-existent model."""
        model = SupportedModels.get_model_by_name("Non-existent Model")
        
        assert model is None
    
    def test_get_models_by_provider(self):
        """Test getting models by provider."""
        google_models = SupportedModels.get_models_by_provider(ModelProvider.GOOGLE)
        
        assert isinstance(google_models, dict)
        assert len(google_models) > 0
        assert all(config.provider == ModelProvider.GOOGLE for config in google_models.values())
    
    def test_get_default_model(self):
        """Test getting the default model."""
        default_model = SupportedModels.get_default_model()
        
        assert default_model is not None
        assert default_model.name == "Gemini 1.5 Flash"


class TestLLMService:
    """Test LLMService class."""
    
    def test_llm_service_initialization(self):
        """Test LLMService initialization."""
        service = LLMService()
        
        assert service.default_model == "Gemini 1.5 Flash"
        assert hasattr(service, 'azure_client')
    
    def test_llm_service_custom_default_model(self):
        """Test LLMService with custom default model."""
        service = LLMService(default_model="Claude 3.5 Sonnet")
        
        assert service.default_model == "Claude 3.5 Sonnet"
    
    def test_list_available_models(self):
        """Test listing available models."""
        service = LLMService()
        models = service.list_available_models()
        
        assert isinstance(models, list)
        assert len(models) > 0
        assert "Gemini 1.5 Flash" in models
    
    def test_get_model_info(self):
        """Test getting model information."""
        service = LLMService()
        info = service.get_model_info("Gemini 1.5 Flash")
        
        assert info is not None
        assert info["name"] == "Gemini 1.5 Flash"
        assert info["provider"] == "google"
    
    def test_get_model_info_not_found(self):
        """Test getting info for non-existent model."""
        service = LLMService()
        info = service.get_model_info("Non-existent Model")
        
        assert info is None
    
    def test_generate_response_unsupported_model(self):
        """Test generating response with unsupported model."""
        service = LLMService()
        
        with pytest.raises(ValueError, match="Unsupported model"):
            service.generate_response("test prompt", model="Unsupported Model")
    
    @patch('src.canvasxpress_gen.llm.service.genai')
    def test_generate_google_response(self, mock_genai):
        """Test generating response with Google model."""
        # Mock the Google API response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Generated response"
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        service = LLMService()
        response = service.generate_response("test prompt", model="Gemini 1.5 Flash")
        
        assert response == "Generated response"
        mock_genai.GenerativeModel.assert_called_once()
        mock_model.generate_content.assert_called_once()
    
    def test_build_config_prompt(self):
        """Test building configuration prompt."""
        service = LLMService()
        
        user_prompt = "Create a bar chart"
        schema_info = "Schema information here"
        few_shot_examples = "Example 1: ..."
        
        full_prompt = service._build_config_prompt(user_prompt, schema_info, few_shot_examples)
        
        assert "Create a bar chart" in full_prompt
        assert "Schema information here" in full_prompt
        assert "Example 1: ..." in full_prompt
        assert "CanvasXpress" in full_prompt
    
    @patch.object(LLMService, 'generate_response')
    def test_generate_json_config_success(self, mock_generate):
        """Test successful JSON config generation."""
        # Mock a valid JSON response
        mock_generate.return_value = '{"data": [], "config": {"graphType": "Bar"}}'
        
        service = LLMService()
        config = service.generate_json_config(
            prompt="Create a bar chart",
            schema_info="Schema info",
            few_shot_examples="Examples"
        )
        
        assert isinstance(config, dict)
        assert "data" in config
        assert "config" in config
        assert config["config"]["graphType"] == "Bar"
    
    @patch.object(LLMService, 'generate_response')
    def test_generate_json_config_invalid_json(self, mock_generate):
        """Test JSON config generation with invalid JSON response."""
        # Mock an invalid JSON response
        mock_generate.return_value = "This is not valid JSON"
        
        service = LLMService()
        
        with pytest.raises(ValueError, match="not valid JSON"):
            service.generate_json_config(
                prompt="Create a bar chart",
                schema_info="Schema info",
                few_shot_examples="Examples"
            )


# Integration tests (these would require actual API keys to run)
@pytest.mark.integration
class TestLLMServiceIntegration:
    """Integration tests for LLM service (require API keys)."""
    
    @pytest.mark.skip(reason="Requires API keys")
    def test_real_google_api_call(self):
        """Test actual Google API call (requires GOOGLE_API_KEY)."""
        service = LLMService()
        response = service.generate_response(
            "Say hello",
            model="Gemini 1.5 Flash",
            max_tokens=10
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.skip(reason="Requires API keys")
    def test_real_config_generation(self):
        """Test actual config generation (requires API keys)."""
        service = LLMService()
        config = service.generate_json_config(
            prompt="Create a simple bar chart with data [1,2,3] and labels ['A','B','C']",
            schema_info="Basic CanvasXpress schema",
            few_shot_examples="Example configurations"
        )
        
        assert isinstance(config, dict)
        assert "data" in config or "config" in config