# CanvasXpress Generation System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

> **Generate CanvasXpress visualizations from natural language descriptions using Large Language Models (LLMs)**

A backend service system that enables users to create scientific visualizations by describing them in plain English. Built with modern architecture and powered by LLMs and RAG (Retrieval Augmented Generation) technology.

## 🌟 Key Features

- **Natural Language Interface**: Describe visualizations in plain English
- **Multi-LLM Support**: Works with OpenAI GPT-4o, Google Gemini, AWS Bedrock, and Ollama
- **RAG-Enhanced Generation**: Uses vector similarity search with BGE-M3 embeddings
- **High Accuracy**: Achieves >97% accuracy through engineered prompts and few-shot examples
- **Backend Service Architecture**: Designed as a service for CanvasXpress integration

## 🚀 Quick Start

### Prerequisites
- Docker
- Make (for using Makefile commands)

### Setup & Run
```bash
git clone https://github.com/buddyroo30/canvasxpress_gen.git
cd canvasxpress_gen
make build
make build_schema_context    # Generate schema information
make build_vector_db         # Create vector database for RAG
make run                     # Run as daemon (or 'make runi' for interactive)
```

### Verify Setup
1. Open browser to `http://localhost:5008` (or your domain if deployed online)
2. Upload a CSV/TSV data file with headers
3. Describe your visualization in plain English

**Example with automotive data:**
- *"Box plot of cty grouped by manufacturer"*
- *"Scatter plot of hwy vs cty colored by drv"*
- *"Area graph of hwy with title 'Highway MPG Distribution'"*

**Note**: This web interface is a quick and easy way to see the system in action and confirm it's working. The production interface is integrated directly into CanvasXpress.

## 🔗 Connecting to CanvasXpress

### Production Integration
Configure CanvasXpress to use your running service:

```javascript
// In your CanvasXpress configuration
var config = {
    // Your existing CanvasXpress configuration
    graphType: "Bar",
    title: "My Visualization",
    
    // Add LLM service configuration
    llmServiceURL: "http://localhost:5008/ask"  // or your domain: "https://your-domain.com:5008/ask"
};

var cx = new CanvasXpress("canvasId", data, config);
```

### API Usage
```bash
curl -X POST http://localhost:5008/ask \
  -F "prompt=Create a scatter plot of hwy vs cty colored by manufacturer" \
  -F "datafile_contents=[[\"manufacturer\",\"hwy\",\"cty\"],[\"toyota\",35,28],[\"ford\",30,25]]"
```

### Public vs Private Deployment
- **Public**: Use the publicly available CanvasXpress instance at canvasxpress.org
- **Private**: Run your own instance for data security within corporate networks

## 📖 System Architecture

### Backend Service Design
This system is designed as a **backend service** for CanvasXpress, not as a traditional Python library. Users interact with the system through:
1. **CanvasXpress Integration**: Primary intended usage via CanvasXpress UI
2. **Direct API Calls**: For custom integrations
3. **Development Interface**: For testing and verification

### Core Components
- **LLM Integration**: Multiple LLM providers through unified interface
- **RAG System**: Vector database (Milvus) with BGE-M3 embeddings for semantic search
- **Guided Autocomplete**: Automatic synthetic example generation (part of main CanvasXpress library)
- **Modular Architecture**: Professional Python package structure

## 🛠️ Configuration

### Environment Variables
Create a `.env` file:
```bash
# LLM API Keys (choose what you need)
GOOGLE_API_KEY=your_google_api_key_here
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint

# RAG Configuration
NUM_FEW_SHOTS=25  # Number of examples to retrieve

# Optional: SiteMinder SSO for enterprise
SMVAL=False  # Set to True for enterprise SSO
```

### LLM Models
Edit `llm_models.json` and copy to `~/.cache/`:
```json
{
  "gemini-1.5-flash": {
    "type": "google_gemini",
    "provider": "google"
  },
  "gpt-4o": {
    "type": "openai", 
    "provider": "openai"
  }
}
```

## 🧪 Testing

The system includes **85+ comprehensive automated tests** covering all components:

```bash
# Run all tests (uses real APIs if configured, mocks otherwise)
python -m pytest

# Run with coverage
python -m pytest --cov=src/canvasxpress_gen --cov-report=term-missing

# Integration tests only
python -m pytest tests/test_integration.py -v
```

**Test Features:**
- ✅ Real API integration when keys available
- ✅ Graceful fallback to mocks when unavailable
- ✅ End-to-end RAG workflow validation
- ✅ Works in fresh environments

For detailed testing instructions, see [TESTING.md](TESTING.md).

## 🔧 Development

### Development Environment
```bash
make build_dev
make run_dev  # Runs on port 5009
```

### Code Organization
The codebase follows Python packaging standards:
```
src/canvasxpress_gen/
├── llm/           # LLM service and model management
├── rag/           # RAG system with embeddings and retrieval
└── utils/         # JSON, text, file, and auth utilities
```

## 📚 Documentation

- **[API Documentation](docs/API.md)**: Complete API reference for service endpoints
- **[Integration Guide](docs/INTEGRATION.md)**: CanvasXpress integration details
- **[Testing Guide](TESTING.md)**: Comprehensive testing instructions
- **[Contributing Guide](CONTRIBUTING.md)**: Development and contribution guidelines

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:
- Development setup and workflow
- Code standards and testing requirements
- Submission process

## 📄 License & Citation

MIT License - see [LICENSE](LICENSE) file.

If you use this software in research, please cite:
```bibtex
@article{smith2024canvasxpress,
  title={Generating Visualizations Conversationally using Guided Autocomplete and LLMs},
  author={Smith, Andrew K and Neuhaus, Isaac},
  year={2024}
}
```

## 🆘 Support

- **Issues**: Report bugs and request features via [GitHub Issues](../../issues)
- **Documentation**: Check this README and linked guides
- **Questions**: Contact maintainers or open a discussion

---

**Ready to integrate natural language visualization generation?** 🚀

[Get Started](#-quick-start) | [API Documentation](docs/API.md) | [Contributing](CONTRIBUTING.md)
