"""
LLM Model Configuration

Defines supported models and their configurations.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class ModelProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    AWS_BEDROCK = "aws_bedrock"
    OLLAMA = "ollama"


@dataclass
class ModelConfig:
    """Configuration for an LLM model."""
    name: str
    provider: ModelProvider
    model_id: str
    max_tokens: int = 2048
    temperature: float = 0.0
    top_p: float = 1.0
    region: Optional[str] = None
    endpoint: Optional[str] = None
    api_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "provider": self.provider.value,
            "model_id": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "region": self.region,
            "endpoint": self.endpoint,
            "api_version": self.api_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        """Create from dictionary representation."""
        return cls(
            name=data["name"],
            provider=ModelProvider(data["provider"]),
            model_id=data["model_id"],
            max_tokens=data.get("max_tokens", 2048),
            temperature=data.get("temperature", 0.0),
            top_p=data.get("top_p", 1.0),
            region=data.get("region"),
            endpoint=data.get("endpoint"),
            api_version=data.get("api_version")
        )


class SupportedModels:
    """Registry of supported models with their default configurations."""
    
    # OpenAI Models
    GPT_4O = ModelConfig(
        name="GPT-4o",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o",
        max_tokens=4096
    )
    
    GPT_4_TURBO = ModelConfig(
        name="GPT-4 Turbo",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4-turbo",
        max_tokens=4096
    )
    
    # Azure OpenAI Models
    AZURE_GPT_4O = ModelConfig(
        name="Azure GPT-4o",
        provider=ModelProvider.AZURE_OPENAI,
        model_id="gpt-4o-global",
        max_tokens=4096,
        api_version="2024-02-01"
    )
    
    # Google Models
    GEMINI_FLASH = ModelConfig(
        name="Gemini 1.5 Flash",
        provider=ModelProvider.GOOGLE,
        model_id="gemini-1.5-flash",
        max_tokens=8192
    )
    
    GEMINI_PRO = ModelConfig(
        name="Gemini 1.5 Pro",
        provider=ModelProvider.GOOGLE,
        model_id="gemini-1.5-pro",
        max_tokens=8192
    )
    
    # AWS Bedrock Models
    CLAUDE_SONNET = ModelConfig(
        name="Claude 3.5 Sonnet",
        provider=ModelProvider.AWS_BEDROCK,
        model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
        max_tokens=4096,
        region="us-east-1"
    )
    
    CLAUDE_OPUS = ModelConfig(
        name="Claude 3 Opus",
        provider=ModelProvider.AWS_BEDROCK,
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        max_tokens=4096,
        region="us-west-2"
    )
    
    MISTRAL_LARGE = ModelConfig(
        name="Mistral Large",
        provider=ModelProvider.AWS_BEDROCK,
        model_id="mistral.mistral-large-2407-v1:0",
        max_tokens=2048,
        region="us-west-2"
    )
    
    TITAN_LARGE = ModelConfig(
        name="Amazon Titan",
        provider=ModelProvider.AWS_BEDROCK,
        model_id="amazon.titan-tg1-large",
        max_tokens=2048,
        region="us-east-1"
    )
    
    # Ollama Models (local deployment)
    LLAMA_3_1_70B = ModelConfig(
        name="Llama 3.1 70B",
        provider=ModelProvider.OLLAMA,
        model_id="llama3.1:70b",
        max_tokens=4096,
        endpoint="http://localhost:11434"
    )
    
    DEEPSEEK_CODER = ModelConfig(
        name="DeepSeek Coder",
        provider=ModelProvider.OLLAMA,
        model_id="deepseek-coder:33b",
        max_tokens=4096,
        endpoint="http://localhost:11434"
    )
    
    @classmethod
    def get_all_models(cls) -> Dict[str, ModelConfig]:
        """Get all supported models as a dictionary."""
        models = {}
        for attr_name in dir(cls):
            attr = getattr(cls, attr_name)
            if isinstance(attr, ModelConfig):
                models[attr.name] = attr
        return models
    
    @classmethod
    def get_model_by_name(cls, name: str) -> Optional[ModelConfig]:
        """Get a model configuration by name or alias."""
        # First check by display name
        models = cls.get_all_models()
        model = models.get(name)
        if model:
            return model
        
        # Then check by alias
        return MODEL_ALIASES.get(name)
    
    @classmethod
    def get_models_by_provider(cls, provider: ModelProvider) -> Dict[str, ModelConfig]:
        """Get all models for a specific provider."""
        all_models = cls.get_all_models()
        return {name: config for name, config in all_models.items() 
                if config.provider == provider}
    
    @classmethod
    def get_default_model(cls) -> ModelConfig:
        """Get the default model (Gemini Flash for free tier)."""
        return cls.GEMINI_FLASH


# Model aliases for backward compatibility
MODEL_ALIASES = {
    "gpt-4o": SupportedModels.GPT_4O,
    "gpt-4-turbo": SupportedModels.GPT_4_TURBO,
    "gpt-4o-global": SupportedModels.AZURE_GPT_4O,
    "gemini-1.5-flash": SupportedModels.GEMINI_FLASH,
    "gemini-1.5-pro": SupportedModels.GEMINI_PRO,
    "claude-3.5-sonnet": SupportedModels.CLAUDE_SONNET,
    "claude-3-opus": SupportedModels.CLAUDE_OPUS,
    "mistral-large": SupportedModels.MISTRAL_LARGE,
    "titan-large": SupportedModels.TITAN_LARGE,
    "llama3.1:70b": SupportedModels.LLAMA_3_1_70B,
    "deepseek-coder": SupportedModels.DEEPSEEK_CODER
}


def get_model_config(model_identifier: str) -> Optional[ModelConfig]:
    """
    Get model configuration by name or alias.
    
    Args:
        model_identifier: Model name or alias
        
    Returns:
        ModelConfig if found, None otherwise
    """
    # Try direct name lookup first
    config = SupportedModels.get_model_by_name(model_identifier)
    if config:
        return config
    
    # Try alias lookup
    return MODEL_ALIASES.get(model_identifier)


def list_available_models() -> Dict[str, str]:
    """
    List all available models with their providers.
    
    Returns:
        Dictionary mapping model names to provider names
    """
    models = SupportedModels.get_all_models()
    return {name: config.provider.value for name, config in models.items()}