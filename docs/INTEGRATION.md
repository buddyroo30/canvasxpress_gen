# CanvasXpress Integration Guide

Guide for connecting the CanvasXpress Generation System backend service with CanvasXpress visualizations.

## Overview

The CanvasXpress Generation System is a **backend service** that generates CanvasXpress configurations from natural language descriptions. It operates as an independent system designed to work with the main CanvasXpress library.

### System Relationship
- **This Generation System**: Provides LLM-powered natural language to CanvasXpress configuration conversion
- **Main CanvasXpress Library**: The guided autocomplete/copilot features are part of the main CanvasXpress library
- **Integration**: This backend service generates configurations that are consumed by CanvasXpress visualizations

## Development Interface vs Production Interface

### Development Interface (Testing)
**Purpose**: Verify that your service is set up correctly before integrating with CanvasXpress

*This is a simple demo/test web UI to quickly try out the system, not intended for production use.*

```bash
# Start the service
make build && make build_schema_context && make build_vector_db && make run
# Access at: http://localhost:5008
```

**Features**:
- File upload for CSV/TSV data
- Natural language prompt testing
- Configuration generation verification
- **Note**: Thumbs up/down feature is a placeholder with no backend implementation

**Usage**:
1. Upload automotive data file
2. Test prompts like: *"Box plot of cty grouped by manufacturer"*
3. Verify JSON configuration is generated correctly

### Production Interface (CanvasXpress Integration)
**Purpose**: Actual user interaction for visualization generation within CanvasXpress

## Connecting to CanvasXpress

### Method 1: Direct Integration
Configure CanvasXpress to automatically use your backend service:

```javascript
// Basic CanvasXpress setup with LLM integration
var config = {
    // Your existing CanvasXpress configuration
    graphType: "Bar",
    title: "My Visualization",
    
    // Add LLM service configuration
    llmServiceURL: "http://localhost:5008/ask",
    
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

### Method 2: Manual API Integration
For custom implementations with full control:

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
        // Note: result.data contains the data, result.config contains the configuration
        new CanvasXpress("canvasId", result.data, result.config);
        return result.config;
    } else {
        throw new Error(result.text || 'Failed to generate visualization');
    }
}

// Usage with automotive data (2D array format)
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

## Deployment Options

### Public Deployment
Use the publicly available CanvasXpress instance:
- **Access**: Available at canvasxpress.org
- **Usage**: Integrated LLM generation already available
- **Data**: Sent to public servers

### Private Deployment
Run your own instance for data security:

```bash
# Set up your private instance
git clone https://github.com/buddyroo30/canvasxpress_gen.git
cd canvasxpress_gen
make build
make build_schema_context
make build_vector_db
make run
```

**Benefits**:
- Data remains within your corporate network/VPN
- Full control over LLM models and configuration
- Compliance with data security requirements

**Configuration**:
```javascript
// Point CanvasXpress to your private instance
var config = {
    llmServiceURL: "https://your-internal-server:5008/ask",
    // ... rest of your configuration
};
```

## Enterprise Integration

### Private Deployment
For enterprise environments, deploy the service within your corporate network:

```javascript
// Point to your internal service
var config = {
    llmServiceURL: "https://viz-api.company.com/ask",
    // ... rest of your CanvasXpress configuration
};
```

**Note**: The service includes optional SiteMinder SSO support via environment variables (`SMVAL=True`) if needed in legacy corporate environments. This is server-side authentication only.

## Complete Integration Example

### HTML Page with CanvasXpress Integration
```html
<!DOCTYPE html>
<html>
<head>
    <title>CanvasXpress with LLM Backend</title>
    <script src="https://www.canvasxpress.org/dist/canvasXpress.min.js"></script>
</head>
<body>
    <div>
        <textarea id="prompt" placeholder="Describe your visualization...">
Box plot of cty grouped by manufacturer
        </textarea>
        <button onclick="generate()">Generate</button>
    </div>
    
    <div id="canvas" style="width: 800px; height: 600px;"></div>
    
    <script>
        // Sample automotive data
        const automotiveData = [
            ["manufacturer", "model", "hwy", "cty", "cyl", "drv"],
            ["toyota", "camry", 35, 28, 4, "f"],
            ["toyota", "corolla", 40, 32, 4, "f"],
            ["ford", "f150", 25, 20, 8, "4"],
            ["ford", "focus", 35, 28, 4, "f"],
            ["honda", "civic", 40, 32, 4, "f"],
            ["honda", "accord", 35, 28, 4, "f"]
        ];
        
        async function generate() {
            const prompt = document.getElementById('prompt').value;
            
            try {
                const formData = new FormData();
                formData.append('prompt', prompt);
                formData.append('datafile_contents', JSON.stringify(automotiveData));
                formData.append('model', 'gemini-1.5-flash');
                
                const response = await fetch('http://localhost:5008/ask', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    new CanvasXpress("canvas", result.data, result.config);
                } else {
                    alert('Generation failed: ' + result.text);
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
    </script>
</body>
</html>
```

## Troubleshooting Connection Issues

### Service Not Accessible
```bash
# Verify service is running
curl http://localhost:5008/
# Should return HTML page
```

### CORS Issues
```javascript
// Ensure proper request configuration
const response = await fetch('http://localhost:5008/ask', {
    method: 'POST',
    body: formData,
    mode: 'cors'
});
```

### Authentication Problems
```bash
# Check service accessibility
curl http://localhost:5008/userinfo
```

### Generation Failures
```javascript
// Try different parameters
const options = {
    model: 'gemini-1.5-flash',  // Faster model
    temperature: 0.1,           // More consistent
    maxTokens: 2048            // More space for complex configs
};
```

## Data Security Considerations

### Private Deployment Benefits
- **Data Privacy**: All data processing happens within your network
- **Compliance**: Meets corporate data security requirements
- **Control**: Full control over LLM models and parameters
- **Customization**: Can add custom few-shot examples for your domain

### Setup for Private Deployment
1. Deploy the backend service within your corporate network
2. Configure CanvasXpress to point to your internal service URL
3. Set up appropriate network security and firewall rules
4. Configure environment variables as needed

---

For complete API reference, see [API Documentation](API.md).