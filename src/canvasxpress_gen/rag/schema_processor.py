"""
Schema processor for CanvasXpress documentation and configuration processing.

This module provides functionality for processing CanvasXpress schema documentation,
generating schema records, and preparing data for vectorization.
"""

from typing import List, Dict, Any, Optional, Tuple
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SchemaField:
    """Represents a CanvasXpress schema field."""
    name: str
    description: Optional[str] = None
    field_type: Optional[str] = None
    category: Optional[str] = None
    options: Optional[List[Any]] = None
    default_value: Optional[Any] = None


@dataclass
class FewShotExample:
    """Represents a few-shot example for training."""
    id: str
    config_english: str
    headers: List[str]
    config: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SchemaProcessor:
    """
    Processor for CanvasXpress schema documentation and few-shot examples.
    
    This class handles parsing CanvasXpress documentation, generating schema records,
    and preparing data for vectorization in the RAG system.
    """
    
    def __init__(self):
        """Initialize the schema processor."""
        self.schema_fields: Dict[str, SchemaField] = {}
        self.few_shot_examples: List[FewShotExample] = []
    
    def load_canvasxpress_docs(self, docs_file: str) -> Dict[str, SchemaField]:
        """
        Load CanvasXpress documentation from JSON file.
        
        Args:
            docs_file: Path to the documentation JSON file
            
        Returns:
            Dictionary of schema fields
            
        Raises:
            FileNotFoundError: If documentation file doesn't exist
            ValueError: If documentation format is invalid
        """
        docs_path = Path(docs_file)
        if not docs_path.exists():
            raise FileNotFoundError(f"Documentation file not found: {docs_file}")
        
        try:
            with open(docs_path, 'r', encoding='utf-8') as f:
                docs_data = json.load(f)
            
            # Extract the 'P' (Properties) section
            if 'P' not in docs_data:
                raise ValueError("Invalid documentation format: missing 'P' section")
            
            cx_config_info = docs_data['P']
            schema_fields = {}
            
            for field_name, field_info in cx_config_info.items():
                # Clean up comment text
                description = None
                if 'C' in field_info:
                    description = field_info['C'].rstrip('<br>')
                
                # Extract field information
                schema_field = SchemaField(
                    name=field_name,
                    description=description,
                    field_type=field_info.get('T'),
                    category=field_info.get('M'),
                    options=field_info.get('O'),
                    default_value=field_info.get('D')
                )
                
                schema_fields[field_name] = schema_field
            
            self.schema_fields = schema_fields
            logger.info(f"Loaded {len(schema_fields)} schema fields from {docs_file}")
            return schema_fields
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in documentation file: {e}")
        except Exception as e:
            logger.error(f"Failed to load documentation: {e}")
            raise
    
    def generate_schema_records(
        self, 
        schema_fields: Optional[Dict[str, SchemaField]] = None
    ) -> List[str]:
        """
        Generate text records from schema fields for vectorization.
        
        Args:
            schema_fields: Dictionary of schema fields (uses loaded fields if None)
            
        Returns:
            List of formatted schema record strings
        """
        fields = schema_fields or self.schema_fields
        if not fields:
            logger.warning("No schema fields available for record generation")
            return []
        
        schema_records = []
        
        for field_name, field in fields.items():
            field_info_parts = []
            
            # Add description
            if field.description:
                field_info_parts.append(f"Description: '{field.description}'")
            
            # Add type
            if field.field_type:
                field_info_parts.append(f"Type: '{field.field_type}'")
            
            # Add category
            if field.category:
                field_info_parts.append(f"Category: '{field.category}'")
            
            # Add options
            if field.options:
                options_str = "[" + ",".join(str(opt) for opt in field.options) + "]"
                field_info_parts.append(f"Options for Field Value: {options_str}")
            
            # Add default value
            if field.default_value is not None:
                field_info_parts.append(f"Default Value: '{field.default_value}'")
            
            # Create record if we have information
            if field_info_parts:
                record = f"{field_name}: " + ", ".join(field_info_parts)
                schema_records.append(record)
        
        logger.debug(f"Generated {len(schema_records)} schema records")
        return schema_records
    
    def load_few_shot_examples(self, examples_file: str) -> List[FewShotExample]:
        """
        Load few-shot examples from JSON file.
        
        Args:
            examples_file: Path to the few-shot examples JSON file
            
        Returns:
            List of few-shot examples
            
        Raises:
            FileNotFoundError: If examples file doesn't exist
            ValueError: If examples format is invalid
        """
        examples_path = Path(examples_file)
        if not examples_path.exists():
            raise FileNotFoundError(f"Examples file not found: {examples_file}")
        
        try:
            with open(examples_path, 'r', encoding='utf-8') as f:
                examples_data = json.load(f)
            
            few_shot_examples = []
            
            for i, example in enumerate(examples_data):
                # Convert boolean strings to actual booleans
                config = self._convert_boolean_dict_values(example.get('config', {}))
                
                few_shot_example = FewShotExample(
                    id=example.get('id', f'example_{i}'),
                    config_english=example.get('configEnglish', ''),
                    headers=example.get('headers', []),
                    config=config,
                    metadata=example.get('metadata', {})
                )
                
                few_shot_examples.append(few_shot_example)
            
            self.few_shot_examples = few_shot_examples
            logger.info(f"Loaded {len(few_shot_examples)} few-shot examples from {examples_file}")
            return few_shot_examples
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in examples file: {e}")
        except Exception as e:
            logger.error(f"Failed to load few-shot examples: {e}")
            raise
    
    def _convert_boolean_dict_values(self, data: Any) -> Any:
        """
        Recursively convert string boolean values to actual booleans.
        
        Args:
            data: Data structure to process
            
        Returns:
            Data structure with converted boolean values
        """
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self._convert_boolean_dict_values(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = self._convert_boolean_dict_values(data[i])
        elif isinstance(data, str):
            if data.lower() == "true":
                return True
            elif data.lower() == "false":
                return False
        
        return data
    
    def prepare_vectorization_data(
        self,
        include_schema: bool = True,
        include_examples: bool = True
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Prepare data for vectorization including both schema and examples.
        
        Args:
            include_schema: Whether to include schema records
            include_examples: Whether to include few-shot examples
            
        Returns:
            Tuple of (texts_to_embed, metadata_list)
        """
        texts_to_embed = []
        metadata_list = []
        
        # Add schema records
        if include_schema and self.schema_fields:
            schema_records = self.generate_schema_records()
            for i, record in enumerate(schema_records):
                texts_to_embed.append(record)
                metadata_list.append({
                    "id": f"schema_{i}",
                    "type": "schema",
                    "content": record
                })
        
        # Add few-shot examples
        if include_examples and self.few_shot_examples:
            for example in self.few_shot_examples:
                # Use the English description as the text to embed
                texts_to_embed.append(example.config_english)
                metadata_list.append({
                    "id": example.id,
                    "type": "example",
                    "configEnglish": example.config_english,
                    "headers": example.headers,
                    "config": example.config,
                    "metadata": example.metadata or {}
                })
        
        logger.info(f"Prepared {len(texts_to_embed)} items for vectorization")
        return texts_to_embed, metadata_list
    
    def get_example_by_id(self, example_id: str) -> Optional[FewShotExample]:
        """
        Get a few-shot example by its ID.
        
        Args:
            example_id: ID of the example to retrieve
            
        Returns:
            FewShotExample if found, None otherwise
        """
        for example in self.few_shot_examples:
            if example.id == example_id:
                return example
        return None
    
    def filter_examples_by_criteria(
        self,
        criteria: Dict[str, Any]
    ) -> List[FewShotExample]:
        """
        Filter few-shot examples based on criteria.
        
        Args:
            criteria: Dictionary of filtering criteria
            
        Returns:
            List of filtered examples
        """
        filtered_examples = []
        
        for example in self.few_shot_examples:
            match = True
            
            # Check each criterion
            for key, value in criteria.items():
                if key == "config_contains":
                    # Check if config contains specific keys/values
                    if not self._config_contains(example.config, value):
                        match = False
                        break
                elif key == "english_contains":
                    # Check if English description contains text
                    if value.lower() not in example.config_english.lower():
                        match = False
                        break
                elif key == "headers_contain":
                    # Check if headers contain specific values
                    if not any(value.lower() in header.lower() for header in example.headers):
                        match = False
                        break
            
            if match:
                filtered_examples.append(example)
        
        return filtered_examples
    
    def _config_contains(self, config: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """
        Check if config contains specified key-value pairs.
        
        Args:
            config: Configuration dictionary to check
            criteria: Criteria dictionary
            
        Returns:
            True if all criteria are met
        """
        for key, value in criteria.items():
            if key not in config:
                return False
            if config[key] != value:
                return False
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about loaded data.
        
        Returns:
            Dictionary containing statistics
        """
        return {
            "schema_fields_count": len(self.schema_fields),
            "few_shot_examples_count": len(self.few_shot_examples),
            "schema_fields": list(self.schema_fields.keys())[:10],  # First 10 fields
            "example_ids": [ex.id for ex in self.few_shot_examples[:10]]  # First 10 IDs
        }
    
    def __repr__(self) -> str:
        """String representation of the schema processor."""
        return (f"SchemaProcessor(fields={len(self.schema_fields)}, "
                f"examples={len(self.few_shot_examples)})")