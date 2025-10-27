"""
JSON Utilities

Functions for handling JSON operations, validation, and similarity calculations.
"""

import json
import re
from typing import Dict, Any, Union


def extract_json_substring(s: str) -> str:
    """
    Extracts a JSON substring from the given string.
    
    Parameters:
    s (str): The input string containing a JSON substring.
    
    Returns:
    str: The JSON substring if found, otherwise an empty string.
    """
    # Find the index of the first '{' and the last '}'
    start_index = s.find('{')
    end_index = s.rfind('}')
    
    # If either '{' or '}' is not found, return an empty string
    if start_index == -1 or end_index == -1 or start_index >= end_index:
        return ""
    
    # Extract the substring that is supposed to be JSON
    json_substring = s[start_index:end_index+1]
    return json_substring


def remove_backtick_text(text: str) -> str:
    """Remove text after backticks (```), commonly used in LLM responses."""
    index = text.find('```')
    if index != -1:
        text = text[:index]
    return text


def clean_llm_response_text(generated_text: str) -> str:
    """
    Clean LLM response text to extract valid JSON.
    
    Args:
        generated_text: Raw text from LLM response
        
    Returns:
        Cleaned JSON string
    """
    # Validate if the LLM response is already valid JSON
    try:
        json.loads(generated_text)
        return generated_text
    except json.JSONDecodeError:
        pass
    
    # Extract JSON substring from the response
    json_substring = extract_json_substring(generated_text)
    return json_substring


class JSONSimilarity:
    """
    Calculate similarity between JSON objects recursively.
    
    This class provides methods to compare JSON configurations and calculate
    similarity scores, which is useful for evaluating LLM-generated configurations
    against known correct answers.
    """
    
    @staticmethod
    def calculate_similarity(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> float:
        """
        Calculate recursive similarity score between two JSON objects.
        
        Args:
            obj1: First JSON object
            obj2: Second JSON object
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if obj1 == obj2:
            return 1.0
        
        if type(obj1) != type(obj2):
            return 0.0
        
        if isinstance(obj1, dict):
            return JSONSimilarity._dict_similarity(obj1, obj2)
        elif isinstance(obj1, list):
            return JSONSimilarity._list_similarity(obj1, obj2)
        else:
            return 1.0 if obj1 == obj2 else 0.0
    
    @staticmethod
    def _dict_similarity(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> float:
        """Calculate similarity between two dictionaries."""
        all_keys = set(dict1.keys()) | set(dict2.keys())
        if not all_keys:
            return 1.0
        
        total_similarity = 0.0
        for key in all_keys:
            if key in dict1 and key in dict2:
                total_similarity += JSONSimilarity.calculate_similarity(dict1[key], dict2[key])
            # Keys that exist in only one dict contribute 0 to similarity
        
        return total_similarity / len(all_keys)
    
    @staticmethod
    def _list_similarity(list1: list, list2: list) -> float:
        """Calculate similarity between two lists."""
        if len(list1) == 0 and len(list2) == 0:
            return 1.0
        
        max_len = max(len(list1), len(list2))
        if max_len == 0:
            return 1.0
        
        total_similarity = 0.0
        for i in range(max_len):
            if i < len(list1) and i < len(list2):
                total_similarity += JSONSimilarity.calculate_similarity(list1[i], list2[i])
            # Elements that exist in only one list contribute 0 to similarity
        
        return total_similarity / max_len


class ConfigValidator:
    """
    Validate CanvasXpress configuration objects.
    
    This class provides methods to validate that generated JSON configurations
    are valid and contain required fields for CanvasXpress visualizations.
    """
    
    REQUIRED_FIELDS = ['data', 'config']
    OPTIONAL_FIELDS = ['afterRender', 'events', 'info']
    
    @staticmethod
    def validate_config(config: Union[str, Dict[str, Any]]) -> tuple[bool, str]:
        """
        Validate a CanvasXpress configuration.
        
        Args:
            config: Configuration as JSON string or dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse JSON string if needed
            if isinstance(config, str):
                config_dict = json.loads(config)
            else:
                config_dict = config
            
            # Check required fields
            missing_fields = []
            for field in ConfigValidator.REQUIRED_FIELDS:
                if field not in config_dict:
                    missing_fields.append(field)
            
            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}"
            
            # Validate data structure
            if not ConfigValidator._validate_data_structure(config_dict.get('data')):
                return False, "Invalid data structure"
            
            # Validate config structure
            if not ConfigValidator._validate_config_structure(config_dict.get('config')):
                return False, "Invalid config structure"
            
            return True, "Valid configuration"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def _validate_data_structure(data: Any) -> bool:
        """Validate the data section of a CanvasXpress config."""
        if not isinstance(data, list):
            return False
        
        if len(data) < 2:
            return False
        
        # First row should be headers (strings)
        if not all(isinstance(item, str) for item in data[0]):
            return False
        
        return True
    
    @staticmethod
    def _validate_config_structure(config: Any) -> bool:
        """Validate the config section of a CanvasXpress config."""
        if not isinstance(config, dict):
            return False
        
        # Should have at least a chart type or similar identifier
        common_fields = ['graphType', 'type', 'plotType']
        has_chart_type = any(field in config for field in common_fields)
        
        return has_chart_type