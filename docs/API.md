# CanvasXpress Generation System API Documentation

REST API documentation for the CanvasXpress Generation System backend service.

## Table of Contents

- [Overview](#overview)
- [Base URLs](#base-urls)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Generate CanvasXpress Configuration](#1-generate-canvasxpress-configuration)
  - [Get Few-Shot Examples](#2-get-few-shot-examples)
  - [Generic LLM Query](#3-generic-llm-query)
  - [User Information](#4-user-information)
- [Integration](#integration)
- [Error Handling](#error-handling)
- [Configuration](#configuration)
  - [Environment Variables](#environment-variables)
  - [Available Models](#available-models)
  - [LLM Parameter Glossary](#llm-parameter-glossary)
- [Realistic Data Examples](#realistic-data-examples)

## Overview

The CanvasXpress Generation System provides a RESTful API that enables CanvasXpress to generate visualizations from natural language descriptions. This is a **backend service** designed for integration with CanvasXpress.

**Prerequisites:** Ensure the system is properly set up and configured before using the API. See the [Setup & Run](../README.md#setup--run) section in README.md for complete instructions.

## Base URLs

- **Production**: `http://localhost:5008/` (or your domain for internet access)
- **Development**: `http://localhost:5009/`

## Authentication

- **Default**: No authentication required
- **Optional**: SiteMinder SSO support available via environment variables if needed

## API Endpoints

### 1. Generate CanvasXpress Configuration

**`POST /ask`** - Main endpoint for visualization generation

#### Request Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description |
| `datafile_contents` | string (JSON) | No* | JSON data array |
| `datafile_upload` | file | No* | CSV/TSV file |
| `header` | string (JSON) | No* | JSON array of column headers only |
| `model` | string | No | LLM model (default: "gpt-4-32k") |
| `temperature` | float | No | Generation temperature (default: 0.0) |
| `max_new_tokens` | integer | No | Max tokens to generate (default: 1024) |
| `topp` | float | No | Top-p sampling (default: 1.0) |
| `presence_penalty` | float | No | Presence penalty (default: 0.0) |
| `frequency_penalty` | float | No | Frequency penalty (default: 0.0) |
| `num_few_shots` | integer | No | RAG examples (default: 25) |
| `filter_prompt_from_few_shots` | boolean | No | Filter exact prompt from examples (default: false) |
| `config_only` | boolean | No | Return config only, no data (default: false) |
| `target` | string | No | Optional target identifier |
| `client` | string | No | Optional client identifier |
| `callback` | string | No | JSONP callback function name |

*At least one data source required (`datafile_contents`, `datafile_upload`, or `header`)

#### Examples with Automotive Data

**File Upload:**
```bash
curl -X POST http://localhost:5008/ask \
  -F "prompt=Box plot of cty grouped by manufacturer" \
  -F "datafile_upload=@automotive_data.csv"
```

**JSON Data:**
```bash
curl -X POST http://localhost:5008/ask \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "prompt=Scatter plot of hwy vs cty colored by drv" \
  -d "datafile_contents=[[\"hwy\",\"cty\",\"drv\"],[35,28,\"f\"],[30,25,\"4\"]]"
```

**Headers Only:**
```bash
curl -X POST http://localhost:5008/ask \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "prompt=Box plot of cty grouped by manufacturer" \
  -d "header=[\"manufacturer\",\"model\",\"hwy\",\"cty\",\"drv\"]"
```

#### Response Format
**Success Response:**
```json
{
  "success": true,
  "config_generated_flag": true,
  "config": {
    "graphType": "Boxplot",
    "yAxis": ["cty"],
    "groupingFactors": ["manufacturer"],
    "title": "City MPG by Manufacturer"
  },
  "data": [
    ["manufacturer", "cty"],
    ["toyota", 28],
    ["ford", 25]
  ],
  "header": ["manufacturer", "cty"],
  "datafilename": "automotive_data.csv",
  "total_time_taken": 2.34,
  "prompt": "Box plot of cty grouped by manufacturer",
  "datetime": "2024-01-15 14:30",
  "target": "optional_target_id",
  "client": "optional_client_id"
}
```

**Error Response:**
```json
{
  "success": false,
  "config_generated_flag": false,
  "text": "Error: you must provide a description of the visualization you want"
}
```

**Notes:**
- `data`, `header`, `datafilename` are omitted when `config_only=true`
- `target` and `client` are included only if provided in request
- Response may be wrapped in JSONP callback if `callback` parameter provided

### 2. Get Few-Shot Examples

**`GET /get_few_shots`** - Retrieve similar examples for a prompt

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | No* | Natural language description to find similar examples |
| `num` | string/integer | No | Number of examples (default: 5) or "all" for all examples |
| `format` | string | No | Response format: "text" or "json" (default: "text") |
| `filter_prompt` | boolean | No | Filter out exact prompt match (default: false) |

*Required unless `num=all`

#### Examples

**Get similar examples:**
```bash
curl "http://localhost:5008/get_few_shots?prompt=scatter plot&num=3&format=json"
```

**Get all examples:**
```bash
curl "http://localhost:5008/get_few_shots?num=all&format=json"
```

**Text format response:**
```bash
curl "http://localhost:5008/get_few_shots?prompt=box plot&num=2&format=text"
```

#### Response Formats

**JSON Format:**
```json
[
  {
    "English Text": "Create a scatter plot of hwy vs cty colored by manufacturer",
    "Headers/Column Names": "manufacturer model hwy cty drv",
    "Answer": "{\"graphType\":\"Scatter\",\"xAxis\":[\"hwy\"],\"yAxis\":[\"cty\"],\"colorBy\":\"manufacturer\"}"
  },
  {
    "English Text": "Box plot of cty grouped by drv",
    "Headers/Column Names": "manufacturer model hwy cty drv",
    "Answer": "{\"graphType\":\"Boxplot\",\"yAxis\":[\"cty\"],\"groupingFactors\":[\"drv\"]}"
  }
]
```

**Text Format:**
```
English Text: Create a scatter plot of hwy vs cty colored by manufacturer; Headers/Column Names: manufacturer model hwy cty drv, Answer: {"graphType":"Scatter","xAxis":["hwy"],"yAxis":["cty"],"colorBy":"manufacturer"}
English Text: Box plot of cty grouped by drv; Headers/Column Names: manufacturer model hwy cty drv, Answer: {"graphType":"Boxplot","yAxis":["cty"],"groupingFactors":["drv"]}
```

### 3. Generic LLM Query

**`POST /ask_generic`** - Send generic prompts to LLM

#### Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Natural language prompt for the LLM |
| `model` | string | No | LLM model (default: "gpt-4-32k") |
| `temperature` | float | No | Generation temperature (default: 0.0) |
| `max_new_tokens` | integer | No | Max tokens to generate (default: 1024) |
| `topp` | float | No | Top-p sampling (default: 1.0) |
| `callback` | string | No | JSONP callback function name |

#### Example
```bash
curl -X POST http://localhost:5008/ask_generic \
  -d "prompt=Explain correlation between highway and city MPG" \
  -d "model=gpt-4-32k" \
  -d "temperature=0.1"
```

#### Response Format
**Success Response:**
```json
{
  "success": true,
  "text": "Highway and city MPG are typically correlated because they both measure fuel efficiency, though highway driving usually yields higher MPG due to consistent speeds and fewer stops.",
  "total_time_taken": 1.23,
  "datetime": "2024-01-15 14:30"
}
```

**Error Response:**
```json
{
  "success": false,
  "text": "Error: you must provide a prompt for the LLM"
}
```

### 4. User Information

**`GET /userinfo`** - Get authentication info (enterprise only)

#### Description
Returns user authentication information when SiteMinder SSO is enabled. Uses implicit SSO cookies for authentication.

#### Parameters
None (uses SSO cookies automatically)

#### Response Format
**With SiteMinder SSO enabled:**
```json
{
  "uid": "john.doe",
  "bmsid": "12345"
}
```

**Without SiteMinder SSO (default):**
```json
{
  "uid": "NA",
  "bmsid": "NA"
}
```

#### Example
```bash
curl http://localhost:5008/userinfo
```

## Integration

For complete integration examples and deployment guidance, see the [Integration Guide](INTEGRATION.md).

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "config_generated_flag": false,
  "text": "Error: No configuration was generated by the LLM"
}
```

### Common Error Messages
| Error Message | Cause | Solution |
|---------------|-------|----------|
| `"Error: you must provide a description of the visualization you want"` | Missing or empty `prompt` parameter | Include a valid `prompt` parameter |
| `"Error: you must upload a data file to visualize or pass in a header"` | No data source provided | Include `datafile_contents`, `datafile_upload`, or `header` parameter |
| `"Error: Generated configuration is invalid"` | LLM generated invalid JSON config | Retry request or try different parameters |
| `"Error generating configuration: [details]"` | LLM service error or generation failure | Check LLM service availability, retry with different model |
| `"Error: you must provide a prompt for the LLM"` | Missing prompt in `/ask_generic` endpoint | Include `prompt` parameter |
| `"Unexpected error: [details]"` | System error | Check logs, retry request |

## Configuration

### Environment Variables
```bash
# LLM API Keys
GOOGLE_API_KEY=your_key
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint

# RAG Configuration
NUM_FEW_SHOTS=25

# Enterprise SSO
SMVAL=False
```

For the complete list of environment variables, see [README.md](../README.md#environment-variables-optional).

### Available Models

**Currently Supported Models:**
```json
{
  "gpt-4-32k": {"type": "openai", "text": "GPT-4 32K (default)"},
  "gemini-1.5-flash": {"type": "google_gemini", "text": "Gemini 1.5 Flash"},
  "gemini-1.5-pro": {"type": "google_gemini", "text": "Gemini 1.5 Pro"},
  "gpt-4o-global": {"type": "azure_openai", "text": "GPT-4o"},
  "anthropic.claude-3-5-sonnet-20240620-v1:0": {"type": "anthropic", "text": "Anthropic Claude Sonnet 3.5"},
  "anthropic.claude-3-opus-20240229-v1:0": {"type": "anthropic", "text": "Anthropic Claude Opus 3"},
  "mistral.mistral-large-2407-v1:0": {"type": "mistral", "text": "Mistral Large 2 (24.07)"},
  "amazon.titan-tg1-large": {"type": "titan", "text": "Amazon Titan TG1 Large"}
}
```

**Service Providers:**
- **Google Gemini**: Direct Google AI API
- **Azure OpenAI**: Microsoft Azure OpenAI Service
- **Anthropic/Mistral/Titan**: AWS Bedrock
- **Ollama**: Local Ollama server (if configured)

**Note:** The `llm_models.json` file contains additional models that may not be fully supported by the current LLM service implementation. Use the models listed above for guaranteed compatibility.

### LLM Parameter Glossary

These parameters allow you to fine-tune the behavior of the LLM for specific use cases, such as generating consistent configurations or creative text. Understanding these parameters helps optimize your API requests for better results:

| Parameter | Description | Effect | Recommended Values |
|-----------|-------------|--------|-------------------|
| `temperature` | Controls randomness in text generation | **Lower (0.0-0.3)**: More focused, deterministic output<br>**Higher (0.7-1.0)**: More creative, varied output | **0.0-0.1** for CanvasXpress configs<br>**0.3-0.7** for creative text |
| `topp` | Controls nucleus sampling (cumulative probability) | **Lower (0.1-0.5)**: More focused vocabulary<br>**Higher (0.8-1.0)**: Broader vocabulary selection | **0.9-1.0** for most use cases |
| `presence_penalty` | Penalizes repeated tokens to encourage diversity | **0.0**: No penalty<br>**Positive**: Reduces repetition<br>**Negative**: Allows more repetition | **0.0-0.6** for balanced output |
| `frequency_penalty` | Penalizes frequent tokens to reduce repetition | **0.0**: No penalty<br>**Positive**: Reduces common words<br>**Negative**: Allows frequent words | **0.0-0.3** for natural text |
| `max_new_tokens` | Maximum number of tokens to generate | Controls output length | **512-1024** for configs<br>**1024-2048** for detailed responses |

**Tips for CanvasXpress Configuration Generation:**
- Use **low temperature (0.0-0.1)** for consistent, accurate configurations
- Keep **max_new_tokens** moderate (512-1024) to avoid overly complex configs
- **presence_penalty** and **frequency_penalty** are typically not needed for config generation

## Realistic Data Examples

The system works with automotive datasets (as used in main CanvasXpress library examples) containing fields like:
- `manufacturer`: toyota, ford, honda, etc.
- `model`: camry, f150, civic, etc.  
- `hwy`: Highway MPG (numeric)
- `cty`: City MPG (numeric)
- `cyl`: Number of cylinders (4, 6, 8)
- `drv`: Drive type (f=front, r=rear, 4=4wd)
- `class`: Vehicle class (compact, suv, pickup)

**Example prompts:**
- *"Box plot of cty grouped by manufacturer"*
- *"Scatter plot of hwy vs cty colored by drv"*
- *"Area graph of hwy with title 'Highway MPG Distribution'"*
- *"Bar chart showing average cty by cyl"*

---

For integration examples, see the [Integration Guide](INTEGRATION.md).