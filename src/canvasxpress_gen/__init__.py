"""
CanvasXpress Generation System

A system for generating CanvasXpress visualizations from natural language descriptions
using Large Language Models (LLMs) and guided autocomplete.
"""

__version__ = "1.0.0"
__author__ = "Andrew K Smith, Isaac Neuhaus"
__email__ = "andrew.smith@bms.com"

from .llm import LLMService
from .rag import RetrievalService, EmbeddingService, VectorStore, SchemaProcessor
from .utils import JSONSimilarity, ConfigValidator

__all__ = [
    "LLMService",
    "RetrievalService",
    "EmbeddingService",
    "VectorStore",
    "SchemaProcessor",
    "JSONSimilarity",
    "ConfigValidator"
]