# CanvasXpress Generation System API Documentation

REST API documentation for the CanvasXpress Generation System backend service.

## Overview

The CanvasXpress Generation System provides a RESTful API that enables CanvasXpress to generate visualizations from natural language descriptions. This is a **backend service** designed for integration with CanvasXpress.

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

```bash
curl "http://localhost:5008/get_few_shots?prompt=scatter plot&num=3&format=json"
```

### 3. Generic LLM Query

**`POST /ask_generic`** - Send generic prompts to LLM

```bash
curl -X POST http://localhost:5008/ask_generic \
  -d "prompt=Explain correlation between highway and city MPG"
```

### 4. User Information

**`GET /userinfo`** - Get authentication info (enterprise only)

## CanvasXpress Integration

### Direct Integration
Configure CanvasXpress to automatically use your API service:

```javascript
// Basic CanvasXpress setup with LLM integration
var config = {
    // Your existing CanvasXpress configuration
    graphType: "Bar",
    title: "My Visualization",
    
    // Add LLM service configuration
    llmServiceURL: "http://localhost:5008/ask",  // or your domain
    
    // Optional: Configure LLM parameters
    llmOptions: {
        model: "gemini-1.5-flash",
        temperature: 0.1,
        maxTokens: 1024
    }
};

// Initialize CanvasXpress
var cx = new CanvasXpress("canvasId", data, config);
```

### Custom Integration
For manual API calls with custom processing:

```javascript
async function generateVisualization(prompt, data) {
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('datafile_contents', JSON.stringify(data));
    
    const response = await fetch('http://localhost:5008/ask', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
        new CanvasXpress("canvasId", result.data, result.config);
        return result.config;
    } else {
        throw new Error(result.text);
    }
}

// Usage with automotive data
const automotiveData = [
    ["manufacturer", "model", "hwy", "cty", "drv"],
    ["toyota", "camry", 35, 28, "f"],
    ["ford", "f150", 25, 20, "4"],
    ["honda", "civic", 40, 32, "f"]
];

generateVisualization(
    "Scatter plot of hwy vs cty colored by manufacturer",
    automotiveData
);
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "config_generated_flag": false,
  "text": "Error: No configuration was generated by the LLM"
}
```

### Common Errors
| Error | Description | Solution |
|-------|-------------|----------|
| `MISSING_PROMPT` | No prompt provided | Include 'prompt' parameter |
| `MISSING_DATA` | No data source | Include data via file or JSON |
| `INVALID_MODEL` | Model not available | Check available models |
| `LLM_ERROR` | Generation failed | Retry with different parameters |

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

### Available Models
Configure in `llm_models.json`:
```json
{
  "gemini-1.5-flash": {"type": "google_gemini", "provider": "google"},
  "gpt-4o": {"type": "openai", "provider": "openai"},
  "gpt-4o-global": {"type": "azure_openai", "provider": "azure"}
}
```

## Development vs Production Interface

### Development Interface
- **Purpose**: Testing and verification that the service is working correctly
- **Access**: `http://localhost:5008` (web UI)
- **Features**: Simple file upload and prompt testing
- **Limitations**: Thumbs up/down feature has no backend implementation (placeholder)

### Production Interface
- **Purpose**: Actual user interaction for visualization generation
- **Access**: Integrated directly into CanvasXpress
- **Features**: Full natural language visualization generation within CanvasXpress
- **Usage**: Configure `llmServiceURL` in CanvasXpress config

## Realistic Data Examples

The system works with automotive datasets containing fields like:
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