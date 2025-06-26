"""
File Utilities

Functions for file operations and data parsing.
"""

import csv
import json
import os
from typing import List, Dict, Any, Optional


def parse_file(filename: str) -> List[List[str]]:
    """
    Parse a CSV or tab-delimited file and return rows as a list of lists.
    
    Args:
        filename: Path to the file to parse
        
    Returns:
        List of rows, where each row is a list of strings
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            # Detect the dialect (CSV vs tab-delimited)
            sample = f.read(1024)
            f.seek(0)
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.reader(f, dialect)
            return [row for row in reader]
    except Exception as e:
        raise IOError(f"Error reading file {filename}: {str(e)}")


def load_json_file(filename: str) -> Dict[str, Any]:
    """
    Load and parse a JSON file.
    
    Args:
        filename: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"JSON file not found: {filename}")
    
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_file(data: Dict[str, Any], filename: str, indent: int = 2) -> None:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filename: Path to save the file
        indent: JSON indentation level
        
    Raises:
        IOError: If there's an error writing the file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise IOError(f"Error writing JSON file {filename}: {str(e)}")


def load_text_file(filename: str) -> str:
    """
    Load a text file and return its contents.
    
    Args:
        filename: Path to the text file
        
    Returns:
        File contents as string
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Text file not found: {filename}")
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise IOError(f"Error reading text file {filename}: {str(e)}")


def save_text_file(content: str, filename: str) -> None:
    """
    Save text content to a file.
    
    Args:
        content: Text content to save
        filename: Path to save the file
        
    Raises:
        IOError: If there's an error writing the file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Error writing text file {filename}: {str(e)}")


def file_exists(filename: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        filename: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(filename) and os.path.isfile(filename)


def get_file_size(filename: str) -> int:
    """
    Get the size of a file in bytes.
    
    Args:
        filename: Path to the file
        
    Returns:
        File size in bytes
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if not file_exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    return os.path.getsize(filename)


def list_files_in_directory(directory: str, extension: Optional[str] = None) -> List[str]:
    """
    List files in a directory, optionally filtered by extension.
    
    Args:
        directory: Directory path to search
        extension: File extension to filter by (e.g., '.json', '.txt')
        
    Returns:
        List of file paths
        
    Raises:
        FileNotFoundError: If the directory doesn't exist
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if extension is None or filename.endswith(extension):
                files.append(filepath)
    
    return sorted(files)


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to create
    """
    os.makedirs(directory, exist_ok=True)


def get_file_extension(filename: str) -> str:
    """
    Get the file extension from a filename.
    
    Args:
        filename: Filename or path
        
    Returns:
        File extension including the dot (e.g., '.json')
    """
    return os.path.splitext(filename)[1].lower()


def is_csv_file(filename: str) -> bool:
    """
    Check if a file is likely a CSV file based on extension and content.
    
    Args:
        filename: Path to the file
        
    Returns:
        True if file appears to be CSV, False otherwise
    """
    if not file_exists(filename):
        return False
    
    # Check extension
    ext = get_file_extension(filename)
    if ext in ['.csv', '.tsv', '.txt']:
        return True
    
    # Check content for CSV-like structure
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            sample = f.read(1024)
            # Look for common CSV delimiters
            delimiters = [',', '\t', ';', '|']
            for delimiter in delimiters:
                if delimiter in sample:
                    return True
    except:
        pass
    
    return False