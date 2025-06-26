"""
Text Utilities

Functions for text processing and manipulation.
"""

import re
from typing import Optional


def empty(text: Optional[str]) -> bool:
    """
    Return True if the text is None or composed of only whitespace, False otherwise.
    
    Args:
        text: Input text to check
        
    Returns:
        True if text is empty or whitespace only, False otherwise
    """
    if text is None:
        return True
    if text.strip() == "":
        return True
    return False


def remove_backtick_text(text: str) -> str:
    """
    Remove text after backticks (```), commonly used in LLM responses.
    
    Args:
        text: Input text
        
    Returns:
        Text with content after backticks removed
    """
    index = text.find('```')
    if index != -1:
        text = text[:index]
    return text


def remove_up_to_first_brace(s: str) -> str:
    """
    Removes everything from the start of the string up to the first '{'.
    
    Parameters:
    s (str): The input string.
    
    Returns:
    str: The modified string with everything up to the first '{' removed.
    """
    # Find the index of the first '{'
    index = s.find('{')
    
    # If '{' is not found, return the original string
    if index == -1:
        return s
    
    # Return the substring starting from the first '{'
    return s[index:]


def remove_after_last_brace(s: str) -> str:
    """
    Removes everything from the end of the string after the last '}'.
    
    Parameters:
    s (str): The input string.
    
    Returns:
    str: The modified string with everything after the last '}' removed.
    """
    # Find the index of the last '}'
    index = s.rfind('}')
    
    # If '}' is not found, return the original string
    if index == -1:
        return s
    
    # Return the substring up to and including the last '}'
    return s[:index+1]


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


def clean_text_for_processing(text: str) -> str:
    """
    Clean text for processing by removing extra whitespace and normalizing.
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common markdown artifacts
    text = text.replace('**', '')
    text = text.replace('__', '')
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length, adding a suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text by replacing multiple spaces with single spaces.
    
    Args:
        text: Input text
        
    Returns:
        Text with normalized whitespace
    """
    return re.sub(r'\s+', ' ', text.strip())


def extract_code_blocks(text: str) -> list[str]:
    """
    Extract code blocks from markdown-style text.
    
    Args:
        text: Text containing code blocks
        
    Returns:
        List of code block contents
    """
    pattern = r'```(?:\w+)?\n?(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: Text containing HTML tags
        
    Returns:
        Text with HTML tags removed
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)