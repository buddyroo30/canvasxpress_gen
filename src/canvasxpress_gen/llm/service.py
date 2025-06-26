"""
LLM Service

Main service class for interacting with various Large Language Models.
"""

import os
import json
import boto3
import openai
from openai import AzureOpenAI
import google.generativeai as genai
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from .models import ModelConfig, ModelProvider, SupportedModels
from ..utils.json_utils import clean_llm_response_text
from ..utils.text_utils import normalize_whitespace

# Load environment variables
load_dotenv()


class LLMService:
    """
    Service for interacting with various Large Language Models.
    
    Supports OpenAI, Azure OpenAI, Google Gemini, AWS Bedrock, and Ollama models.
    """
    
    def __init__(self, default_model: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            default_model: Default model to use if none specified
        """
        self.default_model = default_model or "Gemini 1.5 Flash"
        self._setup_clients()
    
    def _setup_clients(self):
        """Setup API clients for different providers."""
        # Google API setup
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        if google_api_key:
            genai.configure(api_key=google_api_key)
        
        # Azure OpenAI setup
        self.azure_client = None
        if all(os.environ.get(key) for key in ["AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT"]):
            self.azure_client = AzureOpenAI(
                api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
                api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-01"),
                azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
            )
        
        # OpenAI setup
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if openai_api_key:
            openai.api_key = openai_api_key
    
    def generate_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate a response using the specified model.
        
        Args:
            prompt: Input prompt for the model
            model: Model name or identifier
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            **kwargs: Additional model-specific parameters
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If model is not supported
            RuntimeError: If generation fails
        """
        model_name = model or self.default_model
        model_config = SupportedModels.get_model_by_name(model_name)
        
        if not model_config:
            raise ValueError(f"Unsupported model: {model_name}")
        
        # Override config with provided parameters
        if max_tokens is not None:
            model_config.max_tokens = max_tokens
        if temperature is not None:
            model_config.temperature = temperature
        if top_p is not None:
            model_config.top_p = top_p
        
        try:
            if model_config.provider == ModelProvider.GOOGLE:
                return self._generate_google(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.AZURE_OPENAI:
                return self._generate_azure_openai(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.OPENAI:
                return self._generate_openai(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.AWS_BEDROCK:
                return self._generate_bedrock(prompt, model_config, **kwargs)
            elif model_config.provider == ModelProvider.OLLAMA:
                return self._generate_ollama(prompt, model_config, **kwargs)
            else:
                raise ValueError(f"Provider {model_config.provider} not implemented")
                
        except Exception as e:
            raise RuntimeError(f"Failed to generate response with {model_name}: {str(e)}")
    
    def _generate_google(self, prompt: str, config: ModelConfig, **kwargs) -> str:
        """Generate response using Google Gemini models."""
        try:
            model = genai.GenerativeModel(config.model_id)
            
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p
            )
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Google API error: {str(e)}")
    
    def _generate_azure_openai(self, prompt: str, config: ModelConfig, **kwargs) -> str:
        """Generate response using Azure OpenAI models."""
        if not self.azure_client:
            raise RuntimeError("Azure OpenAI client not configured")
        
        try:
            completion = self.azure_client.chat.completions.create(
                model=config.model_id,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                presence_penalty=kwargs.get('presence_penalty', 0.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0.0),
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI API error: {str(e)}")
    
    def _generate_openai(self, prompt: str, config: ModelConfig, **kwargs) -> str:
        """Generate response using OpenAI models."""
        try:
            client = openai.OpenAI()
            
            completion = client.chat.completions.create(
                model=config.model_id,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def _generate_bedrock(self, prompt: str, config: ModelConfig, **kwargs) -> str:
        """Generate response using AWS Bedrock models."""
        try:
            bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=config.region or 'us-east-1'
            )
            
            if "anthropic.claude" in config.model_id:
                return self._generate_bedrock_anthropic(bedrock_runtime, prompt, config)
            elif "mistral" in config.model_id:
                return self._generate_bedrock_mistral(bedrock_runtime, prompt, config)
            elif "amazon.titan" in config.model_id:
                return self._generate_bedrock_titan(bedrock_runtime, prompt, config)
            else:
                raise ValueError(f"Unsupported Bedrock model: {config.model_id}")
                
        except Exception as e:
            raise RuntimeError(f"AWS Bedrock error: {str(e)}")
    
    def _generate_bedrock_anthropic(self, client, prompt: str, config: ModelConfig) -> str:
        """Generate response using Bedrock Anthropic models."""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "temperature": config.temperature,
            "messages": [{
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }]
        })
        
        response = client.invoke_model(
            body=body,
            modelId=config.model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        output_list = response_body.get("content", [])
        
        generated_text = ""
        for output in output_list:
            generated_text += output["text"]
        
        return generated_text
    
    def _generate_bedrock_mistral(self, client, prompt: str, config: ModelConfig) -> str:
        """Generate response using Bedrock Mistral models."""
        conversation = [{
            "role": "user",
            "content": [{"text": prompt}]
        }]
        
        response = client.converse(
            modelId=config.model_id,
            messages=conversation,
            inferenceConfig={
                "maxTokens": config.max_tokens,
                "temperature": config.temperature,
                "topP": config.top_p
            }
        )
        
        return response["output"]["message"]["content"][0]["text"]
    
    def _generate_bedrock_titan(self, client, prompt: str, config: ModelConfig) -> str:
        """Generate response using Bedrock Titan models."""
        body = json.dumps({
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": config.max_tokens,
                "stopSequences": [],
                "temperature": config.temperature,
                "topP": config.top_p
            }
        })
        
        response = client.invoke_model(
            body=body,
            modelId=config.model_id,
            accept='application/json',
            contentType='application/json'
        )
        
        response_body = json.loads(response.get('body').read())
        return response_body['results'][0]['outputText']
    
    def _generate_ollama(self, prompt: str, config: ModelConfig, **kwargs) -> str:
        """Generate response using Ollama models."""
        try:
            endpoint = config.endpoint or "http://localhost:11434"
            url = f"{endpoint}/api/generate"
            
            payload = {
                "model": config.model_id,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": config.max_tokens,
                    "temperature": config.temperature,
                    "top_p": config.top_p
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
    
    def generate_json_config(
        self,
        prompt: str,
        schema_info: str,
        few_shot_examples: str,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate CanvasXpress JSON configuration from natural language.
        
        Args:
            prompt: Natural language description
            schema_info: CanvasXpress schema information
            few_shot_examples: Few-shot examples for context
            model: Model to use for generation
            
        Returns:
            Generated CanvasXpress configuration as dictionary
            
        Raises:
            ValueError: If generated response is not valid JSON
        """
        # Construct the full prompt
        full_prompt = self._build_config_prompt(prompt, schema_info, few_shot_examples)
        
        # Generate response
        response = self.generate_response(full_prompt, model=model)
        
        # Clean and parse the response
        cleaned_response = clean_llm_response_text(response)
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Generated response is not valid JSON: {str(e)}")
    
    def _build_config_prompt(
        self,
        user_prompt: str,
        schema_info: str,
        few_shot_examples: str
    ) -> str:
        """Build the complete prompt for configuration generation."""
        return f"""You are an expert at generating CanvasXpress visualization configurations from natural language descriptions.

SCHEMA INFORMATION:
{schema_info}

FEW-SHOT EXAMPLES:
{few_shot_examples}

USER REQUEST:
{user_prompt}

Generate a valid CanvasXpress JSON configuration that fulfills the user's request. Return only the JSON configuration, no additional text or explanation."""
    
    def list_available_models(self) -> List[str]:
        """List all available models."""
        return list(SupportedModels.get_all_models().keys())
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model."""
        config = SupportedModels.get_model_by_name(model_name)
        return config.to_dict() if config else None