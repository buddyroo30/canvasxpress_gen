"""
Utilities Module

Common utility functions for the CanvasXpress Generation System.
"""

from .json_utils import JSONSimilarity, ConfigValidator, clean_llm_response_text
from .text_utils import (
    extract_json_substring,
    remove_backtick_text,
    empty,
    clean_text_for_processing,
    normalize_whitespace
)
from .file_utils import (
    parse_file,
    load_json_file,
    save_json_file,
    load_text_file,
    file_exists
)
from .auth_utils import (
    random_password,
    generate_api_key,
    hash_password,
    verify_password,
    is_strong_password,
    getSiteMinderUser,
    getSMRedirectUrl,
    empty
)

__all__ = [
    # JSON utilities
    "JSONSimilarity",
    "ConfigValidator",
    "clean_llm_response_text",
    
    # Text utilities
    "extract_json_substring",
    "remove_backtick_text",
    "empty",
    "clean_text_for_processing",
    "normalize_whitespace",
    
    # File utilities
    "parse_file",
    "load_json_file",
    "save_json_file",
    "load_text_file",
    "file_exists",
    
    # Auth utilities
    "random_password",
    "generate_api_key",
    "hash_password",
    "verify_password",
    "is_strong_password",
    "getSiteMinderUser",
    "getSMRedirectUrl",
    "empty"
]