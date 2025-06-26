# Testing Guide

This document provides testing instructions for the CanvasXpress Generation System, addressing the automated testing requirements identified during the JOSS review process.

## 🧪 Overview

The system includes automated unit tests for core functionality as requested by JOSS reviewers:
- **Unit Tests**: Core functionality testing
- **RAG System Tests**: Vector database and retrieval testing
- **JSON Generation Tests**: Configuration generation validation
- **Embedding Tests**: Embedding verification
- **Full System Tests**: End-to-end workflow validation

## 🚀 Quick Start

### Local Testing

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/canvasxpress_gen --cov-report=term-missing
```

### Docker Testing

```bash
# Build test container
docker build --build-arg INSTALL_DEV=true -t canvasxpress-test .

# Run all tests
docker run --rm canvasxpress-test python -m pytest tests/ -v
```

## 📋 Test Structure

### Test Organization
```
tests/
├── test_llm.py          # LLM service tests
├── test_rag.py          # RAG system tests
├── test_utils.py        # Utility function tests
└── __init__.py          # Package initialization
```

### Test Categories

#### **Unit Tests**
- **LLM Service**: Model loading, API calls, response parsing
- **RAG Components**: Embedding generation, vector search, retrieval
- **JSON Generation**: Configuration creation and validation
- **Utilities**: JSON processing, text cleaning, file operations

#### **Integration Tests**
- **Full System Workflow**: English input → JSON configuration validation
- **Component Integration**: Testing interactions between modules
- **Mocked External Services**: LLM provider responses (tests are skipped without API keys)

## 🔧 Running Specific Tests

### By Test File
```bash
# Test LLM components
python -m pytest tests/test_llm.py -v

# Test RAG system
python -m pytest tests/test_rag.py -v

# Test utilities
python -m pytest tests/test_utils.py -v
```

### By Test Markers
```bash
# Run only unit tests
python -m pytest -m unit -v

# Run only integration tests  
python -m pytest -m integration -v

# Skip slow tests
python -m pytest -m "not slow" -v
```

## 📊 Coverage Reporting

### Generate Coverage Reports

```bash
# Terminal coverage report
python -m pytest --cov=src/canvasxpress_gen --cov-report=term-missing tests/

# HTML coverage report
python -m pytest --cov=src/canvasxpress_gen --cov-report=html tests/
# View: open htmlcov/index.html
```

### Coverage Configuration
Coverage is configured in `pytest.ini` with the following settings:
- Source: `src/canvasxpress_gen`
- Minimum coverage: 80%
- Reports: HTML and terminal with missing lines
- Automatic coverage collection during test runs

## 🧩 Test Configuration

### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src/canvasxpress_gen
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

## 🔍 Debugging Test Failures

### Verbose Output
```bash
# Maximum verbosity
python -m pytest tests/ -vvv -s

# Show local variables on failure
python -m pytest tests/ --tb=long --showlocals

# Stop on first failure
python -m pytest tests/ -x
```

## 🚨 Common Issues & Solutions

### **Import Errors**
```bash
# Ensure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

### **Missing Dependencies**
```bash
# Install all development dependencies
pip install -r requirements-dev.txt

# Verify pytest installation
python -m pytest --version
```

### **Docker Issues**
```bash
# Ensure development dependencies are installed in container
docker build --build-arg INSTALL_DEV=true -t canvasxpress-test .

# Check container has pytest
docker run --rm canvasxpress-test python -m pytest --version
```

## 📝 Test Requirements (JOSS Review)

The automated tests address the following requirements identified during JOSS review:

1. **Core Functionality Testing**: Unit tests for key system components
2. **RAG System Validation**: Tests for vector database operations and retrieval
3. **JSON Configuration Generation**: Validation of generated CanvasXpress configurations
4. **Embedding Verification**: Tests for embedding generation and similarity matching
5. **Full System Workflow**: End-to-end tests from English input to JSON output

These tests ensure the reliability and correctness of the system's core functionality as requested by the JOSS reviewers.