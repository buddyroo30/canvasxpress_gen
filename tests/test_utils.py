"""
Tests for utilities module functionality.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open

from src.canvasxpress_gen.utils import (
    JSONSimilarity, ConfigValidator, clean_llm_response_text,
    extract_json_substring, remove_backtick_text, empty,
    parse_file, load_json_file, save_json_file, file_exists,
    random_password, hash_password, verify_password, is_strong_password
)


class TestJSONSimilarity:
    """Test JSONSimilarity class."""
    
    def test_identical_objects(self):
        """Test similarity of identical objects."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"a": 1, "b": 2}
        
        similarity = JSONSimilarity.calculate_similarity(obj1, obj2)
        assert similarity == 1.0
    
    def test_completely_different_objects(self):
        """Test similarity of completely different objects."""
        obj1 = {"a": 1, "b": 2}
        obj2 = {"c": 3, "d": 4}
        
        similarity = JSONSimilarity.calculate_similarity(obj1, obj2)
        assert similarity == 0.0
    
    def test_partially_similar_objects(self):
        """Test similarity of partially similar objects."""
        obj1 = {"a": 1, "b": 2, "c": 3}
        obj2 = {"a": 1, "b": 2, "d": 4}
        
        similarity = JSONSimilarity.calculate_similarity(obj1, obj2)
        # 2 matching keys out of 4 total unique keys = 0.5
        assert similarity == 0.5
    
    def test_nested_objects(self):
        """Test similarity of nested objects."""
        obj1 = {"a": {"x": 1, "y": 2}, "b": 3}
        obj2 = {"a": {"x": 1, "y": 2}, "b": 3}
        
        similarity = JSONSimilarity.calculate_similarity(obj1, obj2)
        assert similarity == 1.0
    
    def test_list_similarity(self):
        """Test similarity of lists."""
        list1 = [1, 2, 3]
        list2 = [1, 2, 3]
        
        similarity = JSONSimilarity.calculate_similarity(list1, list2)
        assert similarity == 1.0
    
    def test_different_types(self):
        """Test similarity of different types."""
        obj1 = {"a": 1}
        obj2 = [1, 2, 3]
        
        similarity = JSONSimilarity.calculate_similarity(obj1, obj2)
        assert similarity == 0.0


class TestConfigValidator:
    """Test ConfigValidator class."""
    
    def test_valid_config_dict(self):
        """Test validation of valid config dictionary."""
        config = {
            "data": [["A", "B"], [1, 2], [3, 4]],
            "config": {"graphType": "Bar"}
        }
        
        is_valid, message = ConfigValidator.validate_config(config)
        assert is_valid
        assert "Valid configuration" in message
    
    def test_valid_config_json_string(self):
        """Test validation of valid config JSON string."""
        config = json.dumps({
            "data": [["A", "B"], [1, 2], [3, 4]],
            "config": {"graphType": "Bar"}
        })
        
        is_valid, message = ConfigValidator.validate_config(config)
        assert is_valid
        assert "Valid configuration" in message
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        config = {"config": {"graphType": "Bar"}}
        
        is_valid, message = ConfigValidator.validate_config(config)
        assert not is_valid
        assert "Missing required fields" in message
        assert "data" in message
    
    def test_invalid_json_string(self):
        """Test validation with invalid JSON string."""
        config = "This is not valid JSON"
        
        is_valid, message = ConfigValidator.validate_config(config)
        assert not is_valid
        assert "Invalid JSON" in message
    
    def test_invalid_data_structure(self):
        """Test validation with invalid data structure."""
        config = {
            "data": "invalid data",
            "config": {"graphType": "Bar"}
        }
        
        is_valid, message = ConfigValidator.validate_config(config)
        assert not is_valid
        assert "Invalid data structure" in message


class TestTextUtils:
    """Test text utility functions."""
    
    def test_empty_function(self):
        """Test empty function."""
        assert empty(None) is True
        assert empty("") is True
        assert empty("   ") is True
        assert empty("text") is False
    
    def test_remove_backtick_text(self):
        """Test removing backtick text."""
        text = "Some text ```code block``` more text"
        result = remove_backtick_text(text)
        assert result == "Some text "
    
    def test_extract_json_substring(self):
        """Test extracting JSON substring."""
        text = "Some text before {\"key\": \"value\"} some text after"
        result = extract_json_substring(text)
        assert result == "{\"key\": \"value\"}"
    
    def test_extract_json_substring_no_json(self):
        """Test extracting JSON substring when no JSON present."""
        text = "No JSON here"
        result = extract_json_substring(text)
        assert result == ""
    
    def test_clean_llm_response_text_valid_json(self):
        """Test cleaning LLM response with valid JSON."""
        response = '{"data": [], "config": {"graphType": "Bar"}}'
        result = clean_llm_response_text(response)
        assert result == response
    
    def test_clean_llm_response_text_with_extra_text(self):
        """Test cleaning LLM response with extra text."""
        response = 'Here is the JSON: {"data": [], "config": {"graphType": "Bar"}} End of response'
        result = clean_llm_response_text(response)
        assert result == '{"data": [], "config": {"graphType": "Bar"}}'


class TestFileUtils:
    """Test file utility functions."""
    
    def test_file_exists(self):
        """Test file existence check."""
        with tempfile.NamedTemporaryFile() as tmp:
            assert file_exists(tmp.name) is True
        
        assert file_exists("/nonexistent/file.txt") is False
    
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data='{"key": "value"}')
    def test_load_json_file(self, mock_file, mock_exists):
        """Test loading JSON file."""
        result = load_json_file("test.json")
        assert result == {"key": "value"}
        mock_file.assert_called_once_with("test.json", 'r', encoding='utf-8')
        mock_exists.assert_called_once_with("test.json")
    
    def test_load_json_file_not_found(self):
        """Test loading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            load_json_file("/nonexistent/file.json")
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.makedirs")
    def test_save_json_file(self, mock_makedirs, mock_file):
        """Test saving JSON file."""
        data = {"key": "value"}
        save_json_file(data, "test.json")
        
        mock_file.assert_called_once_with("test.json", 'w', encoding='utf-8')
        mock_makedirs.assert_called_once()
    
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open, read_data="col1,col2\nval1,val2\nval3,val4")
    @patch("csv.Sniffer")
    def test_parse_file(self, mock_sniffer, mock_file, mock_exists):
        """Test parsing CSV file."""
        # Mock CSV sniffer
        mock_dialect = type('MockDialect', (), {'delimiter': ','})()
        mock_sniffer.return_value.sniff.return_value = mock_dialect
        
        with patch("csv.reader") as mock_reader:
            mock_reader.return_value = [["col1", "col2"], ["val1", "val2"], ["val3", "val4"]]
            
            result = parse_file("test.csv")
            assert len(result) == 3
            assert result[0] == ["col1", "col2"]
            mock_exists.assert_called_once_with("test.csv")


class TestAuthUtils:
    """Test authentication utility functions."""
    
    def test_random_password_length(self):
        """Test random password generation with specific length."""
        password = random_password(12)
        assert len(password) == 12
    
    def test_random_password_minimum_length(self):
        """Test random password with minimum length requirement."""
        with pytest.raises(ValueError):
            random_password(3)  # Less than minimum of 4
    
    def test_random_password_complexity(self):
        """Test random password contains required character types."""
        password = random_password(12)
        
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        assert has_lower
        assert has_upper
        assert has_digit
        assert has_special
    
    def test_hash_and_verify_password(self):
        """Test password hashing and verification."""
        password = "test_password_123!"
        
        hashed, salt = hash_password(password)
        
        assert verify_password(password, hashed, salt) is True
        assert verify_password("wrong_password", hashed, salt) is False
    
    def test_is_strong_password_strong(self):
        """Test strong password validation."""
        password = "StrongPass123!"
        
        is_strong, issues = is_strong_password(password)
        assert is_strong
        assert len(issues) == 0
    
    def test_is_strong_password_weak(self):
        """Test weak password validation."""
        password = "weak"
        
        is_strong, issues = is_strong_password(password)
        assert not is_strong
        assert len(issues) > 0
        assert any("at least 8 characters" in issue for issue in issues)
    
    def test_is_strong_password_common(self):
        """Test common password detection."""
        password = "password"
        
        is_strong, issues = is_strong_password(password)
        assert not is_strong
        assert any("too common" in issue for issue in issues)


# Integration tests
@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utilities."""
    
    def test_full_json_processing_workflow(self):
        """Test complete JSON processing workflow."""
        # Simulate LLM response with extra text
        llm_response = '''
        Here is the generated configuration:
        
        ```json
        {
            "data": [["A", "B"], [1, 2], [3, 4]],
            "config": {
                "graphType": "Bar",
                "title": "Test Chart"
            }
        }
        ```
        
        This should work for your visualization.
        '''
        
        # Clean the response
        cleaned = clean_llm_response_text(llm_response)
        
        # Parse as JSON
        config = json.loads(cleaned)
        
        # Validate the configuration
        is_valid, message = ConfigValidator.validate_config(config)
        
        assert is_valid
        assert config["config"]["graphType"] == "Bar"
        assert config["config"]["title"] == "Test Chart"
    
    def test_config_similarity_comparison(self):
        """Test comparing two similar configurations."""
        config1 = {
            "data": [["A", "B"], [1, 2], [3, 4]],
            "config": {"graphType": "Bar", "title": "Chart 1"}
        }
        
        config2 = {
            "data": [["A", "B"], [1, 2], [3, 4]],
            "config": {"graphType": "Bar", "title": "Chart 2"}
        }
        
        similarity = JSONSimilarity.calculate_similarity(config1, config2)
        
        # Should be high similarity (only title differs)
        # 0.75 is reasonable since 3/4 of the structure is identical
        assert similarity > 0.7
        assert similarity < 1.0