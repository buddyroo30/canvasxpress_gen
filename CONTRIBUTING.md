# Contributing to CanvasXpress Generation System

Thank you for your interest in contributing to the CanvasXpress Generation System! This document provides guidelines for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Getting Help](#getting-help)

## Getting Started

The CanvasXpress Generation System is a tool for generating CanvasXpress visualizations from natural language descriptions using Large Language Models (LLMs) and guided autocomplete.

### Prerequisites

- Python 3.8 or higher
- Docker (for containerized deployment)
- Git
- Access to LLM providers (OpenAI, Google, AWS Bedrock, or Ollama)

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/buddyroo30/canvasxpress_gen.git
   cd canvasxpress_gen
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   AZURE_OPENAI_API_KEY=your_azure_openai_key
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   
   # RAG Configuration
   NUM_FEW_SHOTS=25  # Number of few-shot examples to retrieve
   AZURE_OPENAI_ENDPOINT=your_azure_endpoint
   AZURE_OPENAI_API_VERSION=2024-02-01
   ```

5. **Build the vector database:**
   ```bash
   make build_vector_db
   make build_schema_context
   ```

## How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug fixes**: Fix issues in the codebase
- **Feature enhancements**: Add new functionality
- **Documentation improvements**: Enhance README, code comments, or guides
- **Test coverage**: Add unit tests or integration tests
- **Performance optimizations**: Improve system efficiency
- **Few-shot examples**: Add new training examples for better LLM performance

### Contribution Process

1. **Fork the repository** on GitHub
2. **Create a feature branch** from the main branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Update documentation** as needed
6. **Test your changes** thoroughly
7. **Submit a pull request**

## Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and concise
- Use type hints where appropriate

### Example:

```python
def generate_config(prompt: str, model: str = "gpt-4") -> dict:
    """
    Generate CanvasXpress configuration from natural language prompt.
    
    Args:
        prompt: Natural language description of desired visualization
        model: LLM model to use for generation
        
    Returns:
        Dictionary containing CanvasXpress configuration
        
    Raises:
        ValueError: If prompt is empty or invalid
    """
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    # Implementation here
    return config
```

### File Organization

- Place new modules in appropriate directories under `src/canvasxpress_gen/`
- Keep related functionality together
- Use clear, descriptive file names
- Add `__init__.py` files to make directories proper Python packages

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src/canvasxpress_gen

# Run specific test file
python -m pytest tests/test_llm.py
```

### Writing Tests

- Write unit tests for all new functions
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (API calls, file operations)

### Example Test:

```python
import pytest
from src.canvasxpress_gen.llm import LLMService

def test_generate_config_success():
    """Test successful config generation."""
    service = LLMService()
    result = service.generate_config("Create a bar chart")
    
    assert isinstance(result, dict)
    assert "data" in result
    assert "config" in result

def test_generate_config_empty_prompt():
    """Test error handling for empty prompt."""
    service = LLMService()
    
    with pytest.raises(ValueError, match="Prompt cannot be empty"):
        service.generate_config("")
```

## Submitting Changes

### Pull Request Guidelines

1. **Clear title and description**: Explain what your PR does and why
2. **Reference issues**: Link to related GitHub issues
3. **Small, focused changes**: Keep PRs manageable in size
4. **Update documentation**: Include relevant documentation updates
5. **Add tests**: Ensure new code is tested

### PR Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Other (please describe)

## Testing
- [ ] Added unit tests
- [ ] Tested manually
- [ ] All existing tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs if applicable
- **Screenshots** if relevant

### Feature Requests

For feature requests, please provide:

- **Clear description** of the proposed feature
- **Use case** explaining why it's needed
- **Possible implementation** ideas (if any)
- **Alternatives considered**

## Getting Help

### Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: Contact the maintainers directly for sensitive issues

### Documentation

- **README.md**: Basic setup and usage instructions
- **TESTING.md**: Comprehensive testing guide with 85+ automated tests
- **docs/INTEGRATION.md**: Integration guide with CanvasXpress
- **docs/API.md**: Complete API documentation
- **Paper**: Academic paper describing the system (in `paper/` directory)
- **Code comments**: Inline documentation in the source code

## Development Guidelines

### Adding New LLM Models

To add support for a new LLM provider:

1. Add model configuration to `llm_models.json`
2. Implement the model interface in `src/canvasxpress_gen/llm/`
3. Add appropriate error handling and validation
4. Update documentation and tests

### Adding Few-Shot Examples

To improve system accuracy:

1. Use the guided autocomplete system to generate examples
2. Validate examples work correctly
3. Add to the appropriate few-shot files
4. Regenerate vector database

### Performance Considerations

- Profile code changes for performance impact
- Consider memory usage with large datasets
- Optimize vector database queries
- Cache expensive operations where appropriate

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and professional in all interactions.

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

## Questions?

If you have questions about contributing, please:

1. Check existing documentation
2. Search GitHub issues for similar questions
3. Create a new issue with the "question" label
4. Contact the maintainers directly if needed

Thank you for contributing to the CanvasXpress Generation System!