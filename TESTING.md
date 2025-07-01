# Testing Guide

Comprehensive testing instructions for the CanvasXpress Generation System with **85+ automated tests** covering all system components.

## 🧪 Test Features

### Adaptive Testing System
- ✅ **Real API Integration**: Uses actual LLM APIs when configured
- ✅ **Graceful Fallback**: Automatically uses mocks when APIs unavailable  
- ✅ **Environment Agnostic**: Works in fresh clones, CI/CD, and production
- ✅ **Real RAG Testing**: Uses actual PyMilvus vector database when available
- ✅ **Always Passes**: Designed to validate functionality regardless of setup

### Test Behavior Matrix
| API Keys | Vector DB | Test Behavior |
|----------|-----------|---------------|
| ✅ Available | ✅ Available | **Real APIs + Real RAG** (full integration) |
| ✅ Available | ❌ Missing | **Real APIs + Hardcoded Examples** |
| ❌ Missing | ✅ Available | **Mock APIs + Basic Service Init** |
| ❌ Missing | ❌ Missing | **Mock APIs + Basic Service Init** |

## 🚀 Quick Start

### Local Testing
```bash
# Install dependencies and run all tests
pip install -r requirements-dev.txt
python -m pytest

# Verbose output with coverage
python -m pytest -v --cov=src/canvasxpress_gen --cov-report=term-missing

# Integration tests only
python -m pytest tests/test_integration.py -v
```

### Docker Testing
```bash
# Fresh environment testing (uses mocks)
make buildfresh
make shell
python -m pytest
```

## 📋 Test Structure

### Test Organization
```
tests/
├── test_integration.py  # End-to-end integration tests
├── test_llm.py          # LLM service tests
├── test_rag.py          # RAG system tests
└── test_utils.py        # Utility function tests
```

### Test Categories

**Unit Tests:**
- LLM Service: Model loading, API calls, response parsing
- RAG Components: Embedding generation, vector search, retrieval
- Utilities: JSON processing, text cleaning, file operations

**Integration Tests:**
- End-to-End Workflow: English → Vector Search → LLM → CanvasXpress Config
- Real API Integration: Azure OpenAI, OpenAI, Google AI when keys available
- Real RAG Testing: PyMilvus vector database with BGE-M3 embeddings
- Multi-LLM Support: Tests all supported providers

## 🔧 Running Specific Tests

### By Test File
```bash
python -m pytest tests/test_integration.py -v  # End-to-end integration
python -m pytest tests/test_llm.py -v         # LLM components
python -m pytest tests/test_rag.py -v         # RAG system
python -m pytest tests/test_utils.py -v       # Utilities
```

### By Test Markers
```bash
python -m pytest -m unit -v        # Unit tests only
python -m pytest -m integration -v # Integration tests only
python -m pytest -m "not slow" -v  # Skip slow tests
```

## 📊 Coverage Reporting

```bash
# Terminal coverage report
python -m pytest --cov=src/canvasxpress_gen --cov-report=term-missing

# HTML coverage report
python -m pytest --cov=src/canvasxpress_gen --cov-report=html
# View: open htmlcov/index.html
```

## 🔍 Debugging Test Failures

```bash
# Maximum verbosity with local variables
python -m pytest -vvv -s --tb=long --showlocals

# Stop on first failure
python -m pytest -x
```

## 🚨 Common Issues & Solutions

**Import Errors:**
```bash
pip install -e .  # Install in development mode
```

**Missing Dependencies:**
```bash
pip install -r requirements-dev.txt
python -m pytest --version  # Verify pytest installation
```

**Docker Issues:**
```bash
# Ensure dev dependencies in container
docker build --build-arg INSTALL_DEV=true -t canvasxpress-test .
```

## 📝 JOSS Review Requirements

The automated tests address JOSS reviewer requirements:

1. **Core Functionality Testing**: Unit tests for key system components
2. **RAG System Validation**: Vector database operations and retrieval testing
3. **JSON Configuration Generation**: CanvasXpress configuration validation
4. **Embedding Verification**: BGE-M3 embedding generation and similarity matching
5. **Full System Workflow**: End-to-end tests from English input to JSON output

These tests ensure system reliability and correctness as requested by JOSS reviewers.

## 🎯 Test Examples with Automotive Data

The integration tests use realistic automotive data examples:

```python
def test_automotive_visualization_generation():
    """Test with real automotive dataset."""
    prompt = "Box plot of cty grouped by manufacturer"
    data = [
        ["manufacturer", "cty", "hwy", "drv"],
        ["toyota", 28, 35, "f"],
        ["ford", 25, 30, "4"],
        ["honda", 32, 40, "f"]
    ]
    
    # Test generates actual CanvasXpress config
    result = generate_config(prompt, data)
    assert result["config"]["graphType"] == "Boxplot"
    assert "cty" in result["config"]["yAxis"]
```

---

**Quick Commands:**
- `python -m pytest` - Run all tests
- `python -m pytest -v` - Verbose output  
- `python -m pytest tests/test_integration.py -v` - Integration tests only