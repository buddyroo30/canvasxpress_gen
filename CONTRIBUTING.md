# Contributing to CanvasXpress Generation System

Thank you for considering contributing to the CanvasXpress Generation System! 🎉

This guide provides information about how others can contribute to the project, report issues, and seek support.

## 🚀 Getting Started

**First-time setup:** Follow the complete setup instructions in [README.md](README.md)

**For development:** Use the development setup and commands detailed in the README.md

## 🤝 How To Contribute

### 1. Contributing To The Software

**Types of Contributions:**
- Bug fixes and issue resolution
- Feature enhancements and new functionality
- Documentation improvements
- Test coverage expansion
- Performance optimizations
- Few-shot examples for improved LLM accuracy

**Contribution Process:**
1. **Fork** the repository on GitHub
2. **Create branch**: `git checkout -b feature/your-feature`
3. **Make changes** following our coding standards
4. **Add tests** for new functionality
5. **Run tests**: See [TESTING.md](TESTING.md) for detailed testing instructions
6. **Submit PR** with clear description

### 2. Code Standards

**Keep PRs Small and Focused:**
- Submit small, focused pull requests for easier review
- One feature or fix per PR when possible
- Break large changes into logical, reviewable chunks

Follow Python packaging standards and best practices:

```python
def validate_prompt(prompt: str) -> str:
    """Validate and clean user input prompt.
    
    Args:
        prompt: User's natural language description
        
    Returns:
        Cleaned and validated prompt string
        
    Raises:
        ValueError: If prompt is empty or invalid
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")
    
    return prompt.strip()
```

**Standards:**
- Follow [PEP 8](https://pep8.org/) style guidelines
- Add docstrings to functions and classes
- Use type hints where appropriate
- Keep functions focused and concise

## 🧪 Testing Requirements

All contributions must include appropriate tests. For detailed testing instructions and requirements, see [TESTING.md](TESTING.md).

**Quick summary:**
- Add unit tests for new functionality
- Test both success and failure cases
- Use realistic automotive data examples in tests
- Ensure tests work with and without API keys
- All tests must be run inside the Docker container

## 🐛 Reporting Issues or Problems

### Bug Reports
When reporting bugs, please include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behavior** vs actual behavior
- **Environment details** (OS, Python version, Docker version)
- **Error messages** or logs if applicable
- **Data examples** if relevant (use automotive data format)

**Template:**
```markdown
## Bug Description
Brief description of the issue

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python: [e.g., 3.9.16]
- Docker: [e.g., 20.10.21]

## Error Messages
```
Paste any error messages here
```
```

### Feature Requests
For feature requests, please provide:

- **Clear description** of the proposed feature
- **Use case** explaining why it's needed
- **Possible implementation** ideas (if any)
- **Alternatives considered**

## 🆘 Seeking Support

### Support Channels

1. **GitHub Issues**: For bug reports and feature requests
   - Use appropriate labels (bug, enhancement, question, etc.)
   - Search existing issues before creating new ones

2. **GitHub Discussions**: For questions and general discussion
   - Best for "how-to" questions
   - Community support and knowledge sharing

3. **Direct Contact**: For sensitive issues or security concerns
   - Contact maintainers directly via email (andrewsmith_97@yahoo.com)
   - Use for security vulnerabilities or private matters

### Getting Help

**Before seeking support:**
1. Check [README.md](README.md) and documentation files
2. Search existing GitHub issues
3. Review the [API Documentation](docs/API.md) and [Integration Guide](docs/INTEGRATION.md)
4. Try the development interface at `http://localhost:5009` (dev) or `http://localhost:5008` (production) to verify setup

**When asking for help:**
- Provide clear, specific questions
- Include relevant code examples
- Share error messages and logs
- Describe what you've already tried

## 📚 Contributing to Documentation

When updating documentation:
- Use realistic automotive data examples as in main CanvasXpress library (not fictional data)
- Keep examples concise and practical
- Cross-reference related sections
- Follow existing formatting and style
- Update relevant files: [README.md](README.md), [docs/API.md](docs/API.md), [docs/INTEGRATION.md](docs/INTEGRATION.md), [TESTING.md](TESTING.md)

## 🏗️ Adding New Features

**New LLM Models:**
1. Add configuration to [`llm_models.json`](llm_models.json)
2. Implement interface in [`src/canvasxpress_gen/llm/`](src/canvasxpress_gen/llm/)
3. Add error handling and validation
4. Update tests and documentation

**Few-Shot Examples:**
1. Use guided autocomplete to generate examples (preferred)
2. Validate examples work correctly
3. Add to [`all_few_shots.json`](all_few_shots.json)
4. Rebuild vector database: `make build_vector_db`

**Code Structure:**
```
src/canvasxpress_gen/
├── llm/           # LLM service and model management
├── rag/           # RAG system with embeddings and retrieval
└── utils/         # JSON, text, file, and auth utilities
```

## 📋 Pull Request Guidelines

### PR Checklist
- [ ] Clear title and description
- [ ] References related issues
- [ ] Includes tests for new code
- [ ] Documentation updated
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] No breaking changes (or, if breaking changes are necessary, they are clearly documented in the PR description and release notes)

### PR Review Process
1. Automated tests must pass
2. Code review by maintainers
3. Documentation review
4. Integration testing
5. Merge approval

## 📄 License

By contributing, you agree your contributions will be licensed under the same MIT license as the project.

## 🙏 Recognition

Contributors will be acknowledged in:
- Repository contributors list
- Release notes for significant contributions
- Academic citations where appropriate

---

**Questions?** Check existing documentation, search GitHub issues, or create a new issue with the "question" label.

Thank you for contributing to the CanvasXpress Generation System! 🎉