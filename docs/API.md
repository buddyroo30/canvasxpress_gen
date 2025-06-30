# CanvasXpress Generation System API Documentation

This document provides comprehensive documentation for the CanvasXpress Generation System REST API, including endpoint specifications, integration examples, and connection guides.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL and Versioning](#base-url-and-versioning)
- [API Endpoints](#api-endpoints)
- [Integration Examples](#integration-examples)
- [CanvasXpress Integration](#canvasxpress-integration)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [SDKs and Libraries](#sdks-and-libraries)

## Overview

The CanvasXpress Generation System provides a RESTful API that enables applications to generate CanvasXpress visualizations from natural language descriptions. The API is designed to be simple, reliable, and scalable for both individual and enterprise use.

### Key Features

- **Natural Language Processing**: Convert English descriptions to CanvasXpress configurations
- **Multi-format Support**: Accept CSV, TSV, and JSON data formats
- **RAG-Enhanced Generation**: Leverage retrieval-augmented generation for improved accuracy
- **Multiple LLM Support**: Choose from various language models
- **Enterprise Security**: SiteMinder SSO and secure authentication options

### API Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │───▶│  Flask API       │───▶│  LLM Service    │
│                 │    │    (app.py)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                          │
                              ▼                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │  RAG System      │    │  Vector DB      │
                       │  (Retrieval)     │    │  (Milvus)       │
                       └──────────────────┘    └─────────────────┘
```

## Authentication

### SiteMinder SSO (Enterprise)

When SiteMinder is enabled (`SMVAL=True`), all requests require valid SiteMinder session cookies:

```http
Cookie: SMSESSION=your_session_token
```

### Development Mode

For development and testing (`SMVAL=False`), no authentication is required.

### API Key Authentication (Future)

API key authentication is planned for future releases:

```http
Authorization: Bearer your_api_key
```

## Base URL and Versioning

### Production
```
https://your-domain.com/
```

### Development
```
http://localhost:5008/  # Production container
http://localhost:5009/  # Development container
```

### API Versioning

Currently, the API is unversioned. Future versions will use URL-based versioning:
```
/api/v1/endpoint
```

## API Endpoints

### 1. Home Page

**Endpoint:** `GET /`

**Description:** Returns the main interface for testing and development.

**Response:**
```html
<!DOCTYPE html>
<html>
<!-- CanvasXpress Generation Interface -->
</html>
```

**Usage:**
```bash
curl -X GET http://localhost:5008/
```

---

### 2. Generate CanvasXpress Configuration

**Endpoint:** `POST /ask`

**Description:** Generate a CanvasXpress visualization configuration from natural language description and data.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Natural language description of the desired visualization |
| `datafile_contents` | string (JSON) | No* | JSON string containing data array |
| `header` | string (JSON) | No* | JSON string containing header row |
| `datafile_upload` | file | No* | CSV/TSV file upload |
| `model` | string | No | LLM model to use (default: "gpt-4-32k") |
| `temperature` | float | No | Generation temperature (0.0-1.0, default: 0.0) |
| `max_new_tokens` | integer | No | Maximum tokens to generate (default: 1024) |
| `topp` | float | No | Top-p sampling parameter (default: 1.0) |
| `presence_penalty` | float | No | Presence penalty (default: 0.0) |
| `frequency_penalty` | float | No | Frequency penalty (default: 0.0) |
| `num_few_shots` | integer | No | Number of few-shot examples (default: 25, configurable via NUM_FEW_SHOTS env var) |
| `filter_prompt_from_few_shots` | boolean | No | Filter prompt from examples (default: false) |
| `config_only` | boolean | No | Return only config without data (default: false) |
| `callback` | string | No | JSONP callback function name |

*At least one data source is required: `datafile_contents`, `header`, or `datafile_upload`

#### Request Examples

**Form Data with File Upload:**
```bash
curl -X POST http://localhost:5008/ask \
  -F "prompt=Create a bar chart showing sales by region with title 'Regional Sales'" \
  -F "datafile_upload=@sales_data.csv" \
  -F "model=gemini-1.5-flash" \
  -F "temperature=0.1"
```

**JSON Data:**
```bash
curl -X POST http://localhost:5008/ask \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "prompt=Box plot of values grouped by category" \
  -d "datafile_contents=[[\"Category\",\"Value\"],[\"A\",10],[\"B\",15],[\"A\",12],[\"B\",18]]"
```

**JavaScript/AJAX:**
```javascript
const formData = new FormData();
formData.append('prompt', 'Scatter plot of height vs weight colored by gender');
formData.append('datafile_upload', fileInput.files[0]);
formData.append('model', 'gpt-4o');

fetch('/ask', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

#### Response Format

**Success Response:**
```json
{
  "success": true,
  "config_generated_flag": true,
  "config": {
    "graphType": "Bar",
    "title": "Regional Sales",
    "xAxis": ["North", "South", "East", "West"],
    "data": [100, 150, 120, 180],
    "colorScheme": "CanvasXpress"
  },
  "total_time_taken": 2.34,
  "prompt": "Create a bar chart showing sales by region",
  "datetime": "2024-01-15 14:30",
  "datafilename": "sales_data.csv",
  "data": [
    ["Region", "Sales"],
    ["North", 100],
    ["South", 150],
    ["East", 120],
    ["West", 180]
  ],
  "header": ["Region", "Sales"]
}
```

**Error Response:**
```json
{
  "success": false,
  "config_generated_flag": false,
  "text": "Error: No configuration was generated by the LLM, please try again."
}
```

---

### 3. Generic LLM Query

**Endpoint:** `POST /ask_generic`

**Description:** Send a generic prompt to the LLM without CanvasXpress-specific processing.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Text prompt for the LLM |
| `model` | string | No | LLM model to use |
| `temperature` | float | No | Generation temperature |
| `max_new_tokens` | integer | No | Maximum tokens to generate |
| `topp` | float | No | Top-p sampling parameter |
| `callback` | string | No | JSONP callback function name |

#### Example

```bash
curl -X POST http://localhost:5008/ask_generic \
  -d "prompt=Explain the benefits of data visualization" \
  -d "model=gemini-1.5-flash"
```

**Response:**
```json
{
  "success": true,
  "text": "Data visualization offers several key benefits...",
  "total_time_taken": 1.23,
  "datetime": "2024-01-15 14:30"
}
```

---

### 4. Retrieve Few-Shot Examples

**Endpoint:** `GET|POST /get_few_shots`

**Description:** Retrieve similar few-shot examples based on a prompt.

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prompt` | string | Yes | Query to find similar examples |
| `num` | string | No | Number of examples ("all" or integer, default: 5) |
| `format` | string | No | Response format ("text" or "json", default: "text") |
| `filter_prompt` | boolean | No | Filter out prompt from results |

#### Examples

**Get Similar Examples:**
```bash
curl "http://localhost:5008/get_few_shots?prompt=bar chart&num=3&format=json"
```

**Response:**
```json
[
  {
    "id": "example_1",
    "configEnglish": "Create a bar chart showing categories",
    "headers": ["Category", "Value"],
    "config": {
      "graphType": "Bar",
      "title": "Category Analysis"
    }
  }
]
```

---

### 5. User Information

**Endpoint:** `GET|POST /userinfo`

**Description:** Get current user authentication information.

**Response:**
```json
{
  "uid": "user123",
  "bmsid": "BMS123456"
}
```

---

### 6. Environment Information

**Endpoint:** `GET|POST /getenv`

**Description:** Get environment variables (development only).

**Response:**
```html
<plaintext>
PYTHON_VERSION: 3.9.16
FLASK_ENV: development
...
</plaintext>
```

## Integration Examples

### Python Integration

```python
import requests
import json

class CanvasXpressGenerator:
    def __init__(self, base_url="http://localhost:5008"):
        self.base_url = base_url
    
    def generate_config(self, prompt, data, model="gemini-1.5-flash"):
        """Generate CanvasXpress configuration from natural language."""
        
        payload = {
            'prompt': prompt,
            'datafile_contents': json.dumps(data),
            'model': model,
            'temperature': 0.1
        }
        
        response = requests.post(f"{self.base_url}/ask", data=payload)
        return response.json()
    
    def get_similar_examples(self, prompt, num=5):
        """Get similar few-shot examples."""
        
        params = {
            'prompt': prompt,
            'num': str(num),
            'format': 'json'
        }
        
        response = requests.get(f"{self.base_url}/get_few_shots", params=params)
        return response.json()

# Usage
generator = CanvasXpressGenerator()

data = [
    ["Month", "Sales", "Profit"],
    ["Jan", 100, 20],
    ["Feb", 150, 30],
    ["Mar", 120, 25]
]

result = generator.generate_config(
    prompt="Line chart showing sales and profit over months",
    data=data
)

if result['success']:
    config = result['config']
    print("Generated CanvasXpress config:", json.dumps(config, indent=2))
```

### JavaScript Integration

```javascript
class CanvasXpressAPI {
    constructor(baseUrl = 'http://localhost:5008') {
        this.baseUrl = baseUrl;
    }
    
    async generateConfig(prompt, data, options = {}) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        
        // Add optional parameters
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const response = await fetch(`${this.baseUrl}/ask`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async getSimilarExamples(prompt, num = 5) {
        const params = new URLSearchParams({
            prompt: prompt,
            num: num.toString(),
            format: 'json'
        });
        
        const response = await fetch(`${this.baseUrl}/get_few_shots?${params}`);
        return await response.json();
    }
}

// Usage
const api = new CanvasXpressAPI();

const data = [
    ["Product", "Q1", "Q2", "Q3", "Q4"],
    ["Widget A", 100, 120, 110, 130],
    ["Widget B", 80, 90, 95, 100]
];

api.generateConfig(
    "Stacked bar chart showing quarterly sales by product",
    data,
    { model: 'gpt-4o', temperature: 0.1 }
).then(result => {
    if (result.success) {
        console.log('Generated config:', result.config);
    } else {
        console.error('Generation failed:', result.text);
    }
});
```

### cURL Examples

**Basic Configuration Generation:**
```bash
#!/bin/bash

# Generate CanvasXpress config from CSV file
curl -X POST http://localhost:5008/ask \
  -F "prompt=Create a scatter plot of height vs weight with regression line" \
  -F "datafile_upload=@health_data.csv" \
  -F "model=gemini-1.5-flash" \
  -F "temperature=0.0" \
  | jq '.config'
```

**Batch Processing:**
```bash
#!/bin/bash

# Process multiple visualization requests
prompts=(
  "Bar chart of sales by region"
  "Line chart showing trends over time"
  "Pie chart of market share"
)

for prompt in "${prompts[@]}"; do
  echo "Processing: $prompt"
  curl -s -X POST http://localhost:5008/ask \
    -F "prompt=$prompt" \
    -F "datafile_upload=@data.csv" \
    | jq -r '.success'
done
```

## CanvasXpress Integration

### Direct Integration

CanvasXpress can directly connect to your API instance:

```javascript
// Configure CanvasXpress to use your API
var config = {
    // ... your CanvasXpress configuration
    llmServiceURL: "http://your-server:5008/ask"
};

// CanvasXpress will automatically use this URL for LLM generation
var cx = new CanvasXpress(data, config, "canvasId");
```

### Custom Integration

For more control over the integration:

```javascript
class CanvasXpressLLMIntegration {
    constructor(apiUrl, canvasId) {
        this.apiUrl = apiUrl;
        this.canvasId = canvasId;
    }
    
    async generateVisualization(prompt, data) {
        try {
            // Call your API
            const response = await fetch(`${this.apiUrl}/ask`, {
                method: 'POST',
                body: this.createFormData(prompt, data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Create CanvasXpress visualization
                this.createCanvasXpress(result.config, result.data);
                return result;
            } else {
                throw new Error(result.text);
            }
        } catch (error) {
            console.error('Visualization generation failed:', error);
            throw error;
        }
    }
    
    createFormData(prompt, data) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        return formData;
    }
    
    createCanvasXpress(config, data) {
        // Create CanvasXpress instance with generated config
        new CanvasXpress(data, config, this.canvasId);
    }
}

// Usage
const integration = new CanvasXpressLLMIntegration(
    'http://localhost:5008',
    'myCanvas'
);

integration.generateVisualization(
    "Interactive heatmap with clustering",
    myData
).then(result => {
    console.log('Visualization created successfully');
}).catch(error => {
    console.error('Failed to create visualization:', error);
});
```

### Enterprise Deployment

For enterprise environments with security requirements:

```javascript
// Configure for enterprise deployment
const enterpriseConfig = {
    apiUrl: 'https://internal-viz-api.company.com',
    authentication: {
        type: 'siteminder',
        // SiteMinder cookies will be automatically included
    },
    timeout: 30000,
    retries: 3
};

class EnterpriseCanvasXpressAPI {
    constructor(config) {
        this.config = config;
    }
    
    async generateConfig(prompt, data, options = {}) {
        const requestOptions = {
            method: 'POST',
            body: this.createFormData(prompt, data, options),
            credentials: 'include', // Include cookies for SiteMinder
            timeout: this.config.timeout
        };
        
        let attempts = 0;
        while (attempts < this.config.retries) {
            try {
                const response = await fetch(`${this.config.apiUrl}/ask`, requestOptions);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                return await response.json();
            } catch (error) {
                attempts++;
                if (attempts >= this.config.retries) {
                    throw error;
                }
                
                // Wait before retry
                await new Promise(resolve => setTimeout(resolve, 1000 * attempts));
            }
        }
    }
    
    createFormData(prompt, data, options) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        
        // Add enterprise-specific options
        formData.append('model', options.model || 'gpt-4o');
        formData.append('temperature', options.temperature || '0.1');
        
        return formData;
    }
}
```

## Error Handling

### Error Response Format

All API endpoints return consistent error responses:

```json
{
  "success": false,
  "config_generated_flag": false,
  "text": "Detailed error message",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2024-01-15T14:30:00Z"
}
```

### Common Error Codes

| Error Code | Description | Solution |
|------------|-------------|----------|
| `MISSING_PROMPT` | No prompt provided | Include 'prompt' parameter |
| `MISSING_DATA` | No data source provided | Include data via file, JSON, or headers |
| `INVALID_MODEL` | Specified model not available | Check available models |
| `LLM_ERROR` | LLM generation failed | Retry with different parameters |
| `VALIDATION_ERROR` | Generated config invalid | Retry or adjust prompt |
| `AUTH_ERROR` | Authentication failed | Check SiteMinder session |
| `RATE_LIMIT` | Too many requests | Wait and retry |

### Error Handling Best Practices

```python
import requests
import time
from typing import Optional, Dict, Any

def robust_api_call(
    url: str, 
    data: Dict[str, Any], 
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> Optional[Dict[str, Any]]:
    """Make a robust API call with retry logic."""
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success'):
                return result
            else:
                error_msg = result.get('text', 'Unknown error')
                print(f"API error: {error_msg}")
                
                # Don't retry certain errors
                if 'MISSING_PROMPT' in error_msg or 'MISSING_DATA' in error_msg:
                    return result
                    
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            
        except ValueError as e:
            print(f"JSON decode error: {e}")
            
        # Wait before retry
        if attempt < max_retries - 1:
            wait_time = backoff_factor * (2 ** attempt)
            time.sleep(wait_time)
    
    return None
```

## Rate Limiting

### Current Limits

- **Development**: No rate limiting
- **Production**: Depends on deployment configuration

### Future Rate Limiting

Planned rate limiting structure:

| Tier | Requests/Hour | Requests/Day |
|------|---------------|--------------|
| Free | 100 | 1,000 |
| Basic | 1,000 | 10,000 |
| Enterprise | Unlimited | Unlimited |

### Rate Limit Headers

Future API responses will include rate limit information:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642694400
```

## SDKs and Libraries

### Official SDKs (Planned)

- **Python SDK**: `pip install canvasxpress-gen`
- **JavaScript SDK**: `npm install canvasxpress-gen`
- **R Package**: `install.packages("canvasxpress.gen")`

### Community Libraries

- **PHP Wrapper**: Available on GitHub
- **Java Client**: Community-maintained
- **Go SDK**: In development

### SDK Example (Python - Future)

```python
from canvasxpress_gen import CanvasXpressGenerator

# Initialize client
client = CanvasXpressGenerator(
    api_url="http://localhost:5008",
    model="gemini-1.5-flash"
)

# Generate visualization
result = client.generate(
    prompt="Scatter plot with trend line",
    data=my_data,
    options={
        "temperature": 0.1,
        "style": "scientific"
    }
)

# Use result
if result.success:
    config = result.config
    # Integrate with CanvasXpress
```

## Support and Resources

### Documentation
- **API Reference**: This document
- **Integration Guide**: [Integration Examples](#integration-examples)
- **Error Reference**: [Error Handling](#error-handling)

### Support Channels
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Comprehensive guides and examples
- **Community**: Discussion forums and community support

### Useful Links
- **CanvasXpress Documentation**: https://www.canvasxpress.org/docs/
- **LLM Model Documentation**: Provider-specific documentation
- **Docker Deployment Guide**: Container deployment instructions

---

*This API documentation is maintained alongside the codebase. For the latest updates, please refer to the repository documentation.*