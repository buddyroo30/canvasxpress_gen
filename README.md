# CanvasXpress Generation System

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://docker.com)

> **Generate CanvasXpress visualizations from natural language descriptions using Large Language Models (LLMs)**

A comprehensive system that enables users to create sophisticated scientific visualizations by simply describing them in plain English. Built with a modern, modular architecture and powered by state-of-the-art LLMs and RAG (Retrieval Augmented Generation) technology.

## 🌟 Key Features

- **Natural Language Interface**: Describe visualizations in plain English
- **Multi-LLM Support**: Works with OpenAI GPT-4o, Google Gemini, AWS Bedrock models, and Ollama
- **RAG-Enhanced Generation**: Uses vector similarity search with BGE-M3 embeddings
- **High Accuracy**: Achieves near-perfect accuracy through carefully engineered prompts and few-shot examples
- **Enterprise Ready**: Supports SiteMinder SSO and private deployment
- **Modular Architecture**: Professional Python package structure with automated unit tests
- **Docker-First**: Complete containerized deployment with development and production environments

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Make (for using Makefile commands)
- `~/.cache` directory in your home directory

### Basic Setup

1. **Clone and Build**
   ```bash
   git clone https://github.com/buddyroo30/canvasxpress_gen.git
   cd canvasxpress_gen
   make build
   ```

2. **Initialize System**
   ```bash
   make build_schema_context    # Generate schema information
   make build_vector_db         # Create vector database for RAG
   ```

3. **Run Application**
   ```bash
   make run                     # Run as daemon
   # OR
   make runi                    # Run interactively (recommended for first time)
   ```

4. **Access the System**
   - Open your browser to `http://localhost:5008`
   - Upload a CSV/TSV data file with headers
   - Describe your desired visualization in plain English
   - Example: *"box plot of len on x axis grouped by dose with title 'len by dose'"*

5. **Stop Application**
   ```bash
   make exit
   ```

## 🖥️ Demo Web Interface

The system includes a user-friendly web demo interface for quick experimentation:

- **Access**: Navigate to `http://localhost:5008` (or `http://localhost:5009` for dev)
- **Features**: Interactive chat interface, file upload, parameter controls, and real-time visualization generation
- **No Programming Required**: Simply describe your visualization in natural language
- **Professional UI**: CanvasXpress.org branded interface with export functionality
- **Port Customization**: You can change the default ports by editing the `Makefile`

For detailed usage instructions and screenshots, see the [Demo Web Interface section](docs/INTEGRATION.md#demo-web-interface) in the Integration Guide.

### Development Environment

For development work, use the `_dev` versions of all commands:

```bash
make build_dev
make build_schema_context_dev
make build_vector_db_dev
make run_dev                  # Runs on port 5009
make exit_dev
```

### Testing

The system includes automated unit tests for core functionality as requested by JOSS reviewers. For detailed testing instructions, see [TESTING.md](TESTING.md).

**Quick test commands:**
```bash
# Local testing
python -m pytest tests/ -v

# Docker testing
docker build --build-arg INSTALL_DEV=true -t canvasxpress-test .
docker run --rm canvasxpress-test python -m pytest tests/ -v
```

## 📖 How It Works

The CanvasXpress Generation System is a **standalone service** that generates CanvasXpress configurations from natural language descriptions. It works in conjunction with the main CanvasXpress library but operates independently.

### 🔗 Relationship to CanvasXpress

- **This Repository**: Contains the LLM-powered generation system that creates CanvasXpress configurations from text descriptions
- **Main CanvasXpress**: The guided autocomplete/copilot features described in the JOSS paper are part of the main CanvasXpress library at [github.com/neuhausi/canvasXpress](https://github.com/neuhausi/canvasXpress)
- **Integration**: This generation system can be integrated with CanvasXpress to provide natural language visualization creation capabilities

### 🛠️ System Architecture

The CanvasXpress Generation System combines several advanced technologies:

### 🧠 **LLM Integration**
- Supports multiple LLM providers through a unified interface
- Carefully engineered prompts optimized for visualization generation
- Dynamic model selection based on requirements and availability

### 🔍 **RAG (Retrieval Augmented Generation)**
- Vector database powered by Milvus for similarity search
- BGE-M3 embeddings for semantic understanding
- Automatic retrieval of relevant few-shot examples
- Context-aware prompt construction

### 🏗️ **Modular Architecture**
```
src/canvasxpress_gen/
├── llm/           # LLM service and model management
├── rag/           # RAG system with embeddings and retrieval
├── utils/         # Utilities for JSON, text, file, and auth operations
└── __init__.py    # Clean package interface
```

### 🎯 **Guided Generation Process**
1. **User Input**: Natural language description + data file
2. **Context Retrieval**: RAG system finds relevant examples
3. **Prompt Construction**: Combines user input, context, and schema
4. **LLM Generation**: Produces CanvasXpress JSON configuration
5. **Validation**: Ensures generated config is valid and complete

## 🛠️ Installation & Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# LLM API Keys (choose what you need)
GOOGLE_API_KEY=your_google_api_key_here
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_VERSION=2024-02-01

# Development/Production Mode
DEV=False  # Set to True for development mode

# SiteMinder SSO (optional)
SMVAL=False  # Set to True to enable SiteMinder authentication
```

### LLM Model Configuration

Edit `llm_models.json` to configure available models, then copy to `~/.cache/`:

```json
{
  "gemini-1.5-flash": {
    "type": "google_gemini",
    "provider": "google",
    "description": "Fast and efficient model"
  },
  "gpt-4o": {
    "type": "openai", 
    "provider": "openai",
    "description": "Advanced reasoning model"
  }
}
```

### AWS Bedrock Support

For AWS Bedrock models, ensure AWS credentials are configured:
```bash
# Configure AWS credentials
aws configure
# OR set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## 🏗️ Architecture Overview

### System Components

#### **Flask Application** (`app_refactored.py`)
- Modern class-based architecture
- RESTful API endpoints
- Comprehensive error handling
- SiteMinder SSO integration

#### **LLM Service** (`src/canvasxpress_gen/llm/`)
- **`service.py`**: Unified LLM interface supporting multiple providers
- **`models.py`**: Model registry and configuration management
- Supports OpenAI, Google Gemini, AWS Bedrock, and Ollama

#### **RAG System** (`src/canvasxpress_gen/rag/`)
- **`retrieval_service.py`**: Main RAG orchestration
- **`embedding_service.py`**: BGE-M3 embedding generation
- **`vector_store.py`**: Milvus vector database operations
- **`schema_processor.py`**: CanvasXpress schema and example processing

#### **Utilities** (`src/canvasxpress_gen/utils/`)
- **`json_utils.py`**: JSON similarity and validation
- **`text_utils.py`**: Text processing and cleaning
- **`file_utils.py`**: File parsing and I/O operations
- **`auth_utils.py`**: Authentication and security functions

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main interface for testing and development |
| `/ask` | POST | Generate CanvasXpress config from natural language |
| `/ask_generic` | POST | Generic LLM text generation |
| `/get_few_shots` | GET/POST | Retrieve similar examples |
| `/userinfo` | GET/POST | User authentication information |

## 📊 Key Files and Data

### Core Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `prompt.md` / `prompt_dev.md` | Main LLM prompt templates | Project root |
| `doc.json` / `doc_dev.json` | Complete CanvasXpress schema | Project root |
| `all_few_shots.json` / `all_few_shots_dev.json` | Few-shot training examples | Project root |
| `schema.txt` / `schema_dev.txt` | Generated schema context | `~/.cache/` |
| `canvasxpress_llm.db` / `canvasxpress_llm_dev.db` | Vector database | `~/.cache/` |

### Updating System Data

When you modify the few-shot examples or schema:

```bash
# Update production system
make exit                    # Stop current instance
make build_schema_context    # Regenerate schema
make build_vector_db         # Rebuild vector database
make run                     # Restart application

# Update development system  
make exit_dev
make build_schema_context_dev
make build_vector_db_dev
make run_dev
```

## 🔧 Development

### Setting Up Development Environment

1. **Install in Development Mode**
   ```bash
   pip install -e .
   ```

2. **Run Development Server**
   ```bash
   make build_dev
   make run_dev  # Runs on port 5009
   ```

3. **Code Quality Tools**
   ```bash
   # Linting
   flake8 src/ tests/
   
   # Type checking
   mypy src/
   
   # Code formatting
   black src/ tests/
   ```

### Making Changes

1. **Code Changes**: Modify files in `src/canvasxpress_gen/`
2. **Test Changes**: Add/update tests in `tests/` (see [TESTING.md](TESTING.md))
3. **Rebuild**: `make build_dev` if dependencies changed
4. **Test**: Run test suite to validate changes
5. **Update Data**: Rebuild vector DB if examples changed

### Docker Development

```bash
# Interactive shell in container
make shell      # Production environment
make shell_dev  # Development environment

# Fresh build (no cache)
make buildfresh
make buildfresh_dev
```

## 🔗 Integration with CanvasXpress

### Public Integration
The system is integrated into the main [CanvasXpress](https://www.canvasxpress.org/llm.html) website, allowing users to generate visualizations directly through the CanvasXpress interface.

### Private Deployment
For organizations requiring data privacy:

1. **Deploy Your Instance**
   ```bash
   make build
   make build_schema_context
   make build_vector_db
   make run
   ```

2. **Configure CanvasXpress**
   ```javascript
   // In your CanvasXpress configuration
   config['llmServiceURL'] = "http://your-server:5008/ask";
   ```

3. **API Usage**
   ```bash
   curl -X POST http://your-server:5008/ask \
     -F "prompt=Create a bar chart showing sales by region" \
     -F "datafile_contents=[[\"Region\",\"Sales\"],[\"North\",100],[\"South\",150]]"
   ```

## 🔒 Security & Authentication

### SiteMinder SSO Support
For enterprise environments using SiteMinder:

```bash
# Enable SiteMinder in .env
SMVAL=True
SMLOGIN=https://your-siteminder-login-url
SMTARGET=https://your-redirect-url
SMFAILREGEX=authentication.*failed
SMFETCHFAILREGEX=access.*denied
```

### Security Features
- Input sanitization and validation
- CSRF protection
- Secure session management
- Environment-based configuration
- Docker container isolation

## 📚 Advanced Usage

### Custom Few-Shot Examples

Add your own examples to `all_few_shots.json`:

```json
{
  "id": "custom_example_1",
  "configEnglish": "Create a scatter plot with custom styling",
  "headers": ["x_value", "y_value", "category"],
  "config": {
    "graphType": "Scatter2D",
    "title": "Custom Scatter Plot",
    "colorBy": "category"
  }
}
```

Then rebuild the vector database:
```bash
make build_vector_db
```

### Model Performance Tuning

Adjust model parameters in your API calls:

```python
{
  "model": "gpt-4o",
  "temperature": 0.1,      # Lower for more consistent output
  "max_new_tokens": 2048,  # Adjust based on complexity
  "top_p": 0.9            # Nucleus sampling parameter
}
```

### Monitoring and Debugging

Enable detailed logging:
```bash
# Run interactively to see all output
make runi

# Check container logs
docker logs canvasxpress_gen

# Monitor vector database
ls -la ~/.cache/canvasxpress_llm*
```

## 🤝 Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Development setup and workflow
- Code standards and style guidelines  
- Testing requirements
- Submission process

### Quick Contribution Guide

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** following our coding standards
4. **Add tests** for new functionality
5. **Run the test suite**: `python -m pytest tests/ -v`
6. **Submit a pull request**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📖 Citation

If you use this software in your research, please cite our paper:

```bibtex
@article{smith2024canvasxpress,
  title={Generating CanvasXpress Visualizations from Natural Language Using Large Language Models},
  author={Smith, Andrew K and Neuhaus, Isaac},
  journal={Preprint available at OSF},
  year={2024},
  url={https://osf.io/preprints/osf/kf2xp}
}
```

## 🆘 Support

- **Documentation**: Check this README and [CONTRIBUTING.md](CONTRIBUTING.md)
- **Issues**: Report bugs and request features via [GitHub Issues](../../issues)
- **Questions**: Contact the maintainers or open a discussion

## 🔄 Version History

- **v1.0.0**: Initial release with modular architecture
- **v0.9.x**: Legacy monolithic version
- **Development**: Ongoing improvements and feature additions

## 🙏 Acknowledgments

- **CanvasXpress**: Isaac Neuhaus for the excellent visualization library
- **BGE-M3**: BAAI for the embedding model
- **Milvus**: For the vector database technology
- **Community**: Contributors and users who help improve the system

---

**Ready to transform your data visualization workflow?** 🚀

[Get Started](#-quick-start) | [API Documentation](docs/API.md) | [Contributing](CONTRIBUTING.md)
