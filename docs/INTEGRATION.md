# CanvasXpress Integration Guide

This guide provides detailed instructions for integrating the CanvasXpress Generation System with CanvasXpress visualizations, including setup, configuration, and advanced usage patterns.

## Table of Contents

- [Demo Web Interface](#demo-web-interface)
- [Overview](#overview)
- [Quick Integration](#quick-integration)
- [Configuration Options](#configuration-options)
- [Integration Patterns](#integration-patterns)
- [Enterprise Deployment](#enterprise-deployment)
- [Troubleshooting](#troubleshooting)
- [Advanced Examples](#advanced-examples)

## Demo Web Interface

The CanvasXpress Generation System includes a user-friendly web demo interface that allows users to quickly try out the system without any programming knowledge. This interface provides an intuitive way to generate CanvasXpress visualizations using natural language descriptions.

### Accessing the Demo

The demo interface is available when running the system locally:

```bash
# Start the system
make build
make build_schema_context
make build_vector_db
make run

# Access the demo at:
# http://localhost:5008 (production)
# http://localhost:5009 (development - use make run_dev)
```

**Note**: You can customize the default ports by editing the `Makefile` if needed.

### Demo Features

- **Natural Language Input**: Describe your desired visualization in plain English
- **File Upload Support**: Upload CSV, TSV, TXT, or JSON data files
- **Interactive Chat Interface**: Conversational interface with AI assistant
- **Real-time Visualization**: Immediate CanvasXpress chart generation
- **Parameter Controls**: Adjust LLM settings (temperature, tokens, etc.)
- **Professional Styling**: CanvasXpress.org branded interface
- **Export Functionality**: Copy generated configurations for use in your applications

### Using the Demo

1. **Upload Your Data**: Click "Choose File" to upload your dataset (CSV, TSV, TXT, or JSON format)
2. **Describe Your Visualization**: Type a natural language description like:
   - "Create a bar chart showing sales by region"
   - "Make a scatter plot of height vs weight with correlation"
   - "Generate a heatmap of gene expression data with clustering"
3. **Adjust Settings**: Use the sidebar to configure:
   - LLM model selection
   - Temperature (creativity level)
   - Max tokens (response length)
   - Top P, Top K, and penalty parameters
4. **Generate**: Click "Ask" to generate your visualization
5. **Copy Configuration**: Use the "Copy Config" button to get the JSON configuration for your own applications

### Demo Interface Components

- **Main Chat Area**: Interactive conversation with the AI assistant
- **File Upload Section**: Drag-and-drop or click to upload data files
- **Settings Sidebar**: Configure LLM parameters and model selection
- **Control Buttons**: Ask, Clear Chat, and Clear All functionality
- **Responsive Design**: Works on desktop and mobile devices

### Example Prompts

The demo works best with clear, descriptive prompts:

```
Good prompts:
- "Interactive bar chart with hover tooltips showing quarterly sales data"
- "Scatter plot with regression line comparing temperature and humidity"
- "Clustered heatmap of gene expression with dendrograms"
- "Multi-series line chart showing stock prices over time"

Less effective prompts:
- "Make a chart"
- "Visualize this"
- "Show me the data"
```

### Technical Notes

- The demo uses the same API endpoints as the integration examples below
- Generated configurations can be directly used in production CanvasXpress applications
- The interface includes error handling and user feedback for failed generations
- All processing happens server-side; no data is stored permanently

## Overview

The CanvasXpress Generation System is a **standalone service** that generates CanvasXpress configurations from natural language descriptions. It is designed to work with the main CanvasXpress library but operates as an independent system.

### System Relationship

- **This Generation System**: Provides LLM-powered natural language to CanvasXpress configuration conversion
- **Main CanvasXpress Library**: The guided autocomplete/copilot features mentioned in the JOSS paper are part of the main CanvasXpress library ([github.com/neuhausi/canvasXpress](https://github.com/neuhausi/canvasXpress))
- **Complementary Functionality**: This system generates configurations that are consumed by CanvasXpress visualizations

### Integration Patterns

The CanvasXpress Generation System can be integrated with CanvasXpress in several ways:

1. **Direct Integration**: CanvasXpress automatically calls your API service
2. **Custom Integration**: Manual API calls with custom processing
3. **Embedded Integration**: Embedded within existing applications
4. **Enterprise Integration**: Secure deployment within corporate networks

## Quick Integration

### 1. Basic Setup

First, ensure your CanvasXpress Generation System is running:

```bash
# Start the service
make build
make build_schema_context
make build_vector_db
make run

# Verify it's running
curl http://localhost:5008/
```

### 2. Configure CanvasXpress

Add the LLM service URL to your CanvasXpress configuration:

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
var cx = new CanvasXpress(data, config, "canvasId");
```

### 3. Enable Natural Language Interface

```html
<!DOCTYPE html>
<html>
<head>
    <title>CanvasXpress with LLM</title>
    <script src="https://www.canvasxpress.org/dist/canvasXpress.min.js"></script>
</head>
<body>
    <div id="canvasContainer" style="width: 800px; height: 600px;"></div>
    
    <div id="llmInterface">
        <textarea id="promptInput" placeholder="Describe your visualization..."></textarea>
        <button onclick="generateVisualization()">Generate</button>
    </div>

    <script>
        // Your data
        var data = {
            "y": {
                "vars": ["Gene1", "Gene2", "Gene3"],
                "smps": ["Sample1", "Sample2", "Sample3"],
                "data": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
            }
        };

        // Configuration with LLM service
        var config = {
            llmServiceURL: "http://localhost:5008/ask"
        };

        // Initialize CanvasXpress
        var cx = new CanvasXpress(data, config, "canvasContainer");

        function generateVisualization() {
            var prompt = document.getElementById('promptInput').value;
            
            // CanvasXpress will automatically handle the LLM call
            cx.generateFromPrompt(prompt);
        }
    </script>
</body>
</html>
```

## Configuration Options

### LLM Service Configuration

```javascript
var config = {
    // Required: LLM service endpoint
    llmServiceURL: "http://your-server:5008/ask",
    
    // Optional: LLM parameters
    llmOptions: {
        model: "gemini-1.5-flash",        // LLM model to use
        temperature: 0.1,                 // Generation randomness (0.0-1.0)
        maxTokens: 1024,                  // Maximum response length
        topP: 0.9,                        // Nucleus sampling parameter
        numFewShots: 25,                  // Number of examples to use
        filterPrompt: true,               // Filter prompt from examples
        configOnly: false                 // Return only config (no data)
    },
    
    // Optional: Request configuration
    requestOptions: {
        timeout: 30000,                   // Request timeout (ms)
        retries: 3,                       // Number of retry attempts
        retryDelay: 1000                  // Delay between retries (ms)
    },
    
    // Optional: Authentication
    authentication: {
        type: "siteminder",               // Authentication type
        credentials: "include"            // Include credentials in requests
    }
};
```

### Environment-Specific Configuration

```javascript
// Development configuration
var devConfig = {
    llmServiceURL: "http://localhost:5009/ask",
    llmOptions: {
        model: "gemini-1.5-flash",
        temperature: 0.2
    },
    debug: true
};

// Production configuration
var prodConfig = {
    llmServiceURL: "https://viz-api.company.com/ask",
    llmOptions: {
        model: "gpt-4o",
        temperature: 0.1
    },
    authentication: {
        type: "siteminder",
        credentials: "include"
    },
    requestOptions: {
        timeout: 45000,
        retries: 5
    }
};

// Use appropriate config based on environment
var config = (window.location.hostname === 'localhost') ? devConfig : prodConfig;
```

## Integration Patterns

### 1. Direct API Integration

For maximum control over the integration process:

```javascript
class CanvasXpressLLMManager {
    constructor(apiUrl, containerId) {
        this.apiUrl = apiUrl;
        this.containerId = containerId;
        this.currentVisualization = null;
    }
    
    async generateVisualization(prompt, data, options = {}) {
        try {
            // Show loading state
            this.showLoading();
            
            // Call LLM API
            const config = await this.callLLMAPI(prompt, data, options);
            
            // Create visualization
            this.currentVisualization = new CanvasXpress(
                data, 
                config, 
                this.containerId
            );
            
            // Hide loading state
            this.hideLoading();
            
            return this.currentVisualization;
            
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }
    
    async callLLMAPI(prompt, data, options) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        
        // Add options
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const response = await fetch(`${this.apiUrl}/ask`, {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.text || 'Generation failed');
        }
        
        return result.config;
    }
    
    showLoading() {
        const container = document.getElementById(this.containerId);
        container.innerHTML = '<div class="loading">Generating visualization...</div>';
    }
    
    hideLoading() {
        // Loading will be replaced by CanvasXpress visualization
    }
    
    handleError(error) {
        const container = document.getElementById(this.containerId);
        container.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        console.error('Visualization generation failed:', error);
    }
}

// Usage
const manager = new CanvasXpressLLMManager('http://localhost:5008', 'myCanvas');

manager.generateVisualization(
    "Interactive heatmap with hierarchical clustering",
    myGeneExpressionData,
    { model: 'gpt-4o', temperature: 0.1 }
).then(visualization => {
    console.log('Visualization created successfully');
}).catch(error => {
    console.error('Failed to create visualization:', error);
});
```

### 2. Batch Processing Integration

For processing multiple visualizations:

```javascript
class BatchVisualizationProcessor {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.queue = [];
        this.processing = false;
    }
    
    addVisualization(prompt, data, containerId, options = {}) {
        this.queue.push({ prompt, data, containerId, options });
        
        if (!this.processing) {
            this.processQueue();
        }
    }
    
    async processQueue() {
        this.processing = true;
        
        while (this.queue.length > 0) {
            const item = this.queue.shift();
            
            try {
                await this.generateSingleVisualization(item);
                
                // Add delay between requests to avoid overwhelming the API
                await this.delay(1000);
                
            } catch (error) {
                console.error(`Failed to process visualization for ${item.containerId}:`, error);
                this.showError(item.containerId, error.message);
            }
        }
        
        this.processing = false;
    }
    
    async generateSingleVisualization({ prompt, data, containerId, options }) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const response = await fetch(`${this.apiUrl}/ask`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            new CanvasXpress(data, result.config, containerId);
        } else {
            throw new Error(result.text);
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `<div class="error">Error: ${message}</div>`;
    }
}

// Usage
const processor = new BatchVisualizationProcessor('http://localhost:5008');

// Add multiple visualizations to the queue
processor.addVisualization(
    "Bar chart of gene expression levels",
    geneData1,
    "canvas1"
);

processor.addVisualization(
    "Scatter plot with correlation analysis",
    correlationData,
    "canvas2"
);

processor.addVisualization(
    "Heatmap with clustering",
    heatmapData,
    "canvas3"
);
```

### 3. Interactive Dashboard Integration

For building interactive dashboards:

```javascript
class CanvasXpressDashboard {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
        this.visualizations = new Map();
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // Handle prompt submissions
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('llm-prompt-form')) {
                e.preventDefault();
                this.handlePromptSubmission(e.target);
            }
        });
        
        // Handle data uploads
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('data-upload')) {
                this.handleDataUpload(e.target);
            }
        });
    }
    
    async handlePromptSubmission(form) {
        const formData = new FormData(form);
        const containerId = form.dataset.containerId;
        
        try {
            const result = await this.generateVisualization(formData);
            
            if (result.success) {
                this.createVisualization(containerId, result.data, result.config);
                this.updateVisualizationList(containerId, formData.get('prompt'));
            } else {
                this.showError(containerId, result.text);
            }
        } catch (error) {
            this.showError(containerId, error.message);
        }
    }
    
    async generateVisualization(formData) {
        const response = await fetch(`${this.apiUrl}/ask`, {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    createVisualization(containerId, data, config) {
        // Destroy existing visualization if present
        if (this.visualizations.has(containerId)) {
            this.visualizations.get(containerId).destroy();
        }
        
        // Create new visualization
        const viz = new CanvasXpress(data, config, containerId);
        this.visualizations.set(containerId, viz);
        
        // Add export functionality
        this.addExportControls(containerId, viz);
    }
    
    addExportControls(containerId, visualization) {
        const container = document.getElementById(containerId);
        const controls = document.createElement('div');
        controls.className = 'export-controls';
        controls.innerHTML = `
            <button onclick="dashboard.exportVisualization('${containerId}', 'png')">Export PNG</button>
            <button onclick="dashboard.exportVisualization('${containerId}', 'svg')">Export SVG</button>
            <button onclick="dashboard.exportVisualization('${containerId}', 'pdf')">Export PDF</button>
        `;
        container.appendChild(controls);
    }
    
    exportVisualization(containerId, format) {
        const viz = this.visualizations.get(containerId);
        if (viz) {
            viz.export(format);
        }
    }
    
    updateVisualizationList(containerId, prompt) {
        const list = document.getElementById('visualization-list');
        if (list) {
            const item = document.createElement('div');
            item.innerHTML = `
                <div class="viz-item">
                    <span>${prompt}</span>
                    <button onclick="dashboard.removeVisualization('${containerId}')">Remove</button>
                </div>
            `;
            list.appendChild(item);
        }
    }
    
    removeVisualization(containerId) {
        if (this.visualizations.has(containerId)) {
            this.visualizations.get(containerId).destroy();
            this.visualizations.delete(containerId);
            
            const container = document.getElementById(containerId);
            container.innerHTML = '';
        }
    }
    
    showError(containerId, message) {
        const container = document.getElementById(containerId);
        container.innerHTML = `<div class="error">Error: ${message}</div>`;
    }
}

// Initialize dashboard
const dashboard = new CanvasXpressDashboard('http://localhost:5008');
```

## Enterprise Deployment

### 1. Secure Configuration

```javascript
// Enterprise-grade configuration
const enterpriseConfig = {
    // Use HTTPS in production
    llmServiceURL: "https://viz-api.internal.company.com/ask",
    
    // Authentication configuration
    authentication: {
        type: "siteminder",
        validateSession: true,
        sessionTimeout: 3600000, // 1 hour
        renewSession: true
    },
    
    // Security headers
    requestHeaders: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-Token': getCsrfToken(),
        'Content-Security-Policy': "default-src 'self'"
    },
    
    // Request configuration
    requestOptions: {
        timeout: 45000,
        retries: 5,
        retryDelay: 2000,
        maxRetryDelay: 10000,
        backoffFactor: 2
    },
    
    // Error handling
    errorHandling: {
        showUserFriendlyMessages: true,
        logErrors: true,
        reportErrors: true,
        fallbackBehavior: "graceful"
    },
    
    // Performance optimization
    performance: {
        cacheResults: true,
        cacheTTL: 300000, // 5 minutes
        batchRequests: true,
        maxBatchSize: 10
    }
};
```

### 2. Load Balancing and High Availability

```javascript
class EnterpriseCanvasXpressAPI {
    constructor(config) {
        this.config = config;
        this.endpoints = config.endpoints || [config.llmServiceURL];
        this.currentEndpointIndex = 0;
        this.failedEndpoints = new Set();
        this.cache = new Map();
    }
    
    async generateVisualization(prompt, data, options = {}) {
        const cacheKey = this.getCacheKey(prompt, data, options);
        
        // Check cache first
        if (this.config.performance.cacheResults && this.cache.has(cacheKey)) {
            const cached = this.cache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.config.performance.cacheTTL) {
                return cached.result;
            }
        }
        
        // Try endpoints with failover
        let lastError;
        for (let attempt = 0; attempt < this.endpoints.length; attempt++) {
            const endpoint = this.getNextEndpoint();
            
            try {
                const result = await this.callEndpoint(endpoint, prompt, data, options);
                
                // Cache successful result
                if (this.config.performance.cacheResults) {
                    this.cache.set(cacheKey, {
                        result: result,
                        timestamp: Date.now()
                    });
                }
                
                // Mark endpoint as healthy
                this.failedEndpoints.delete(endpoint);
                
                return result;
                
            } catch (error) {
                lastError = error;
                this.failedEndpoints.add(endpoint);
                
                // Log error for monitoring
                if (this.config.errorHandling.logErrors) {
                    console.error(`Endpoint ${endpoint} failed:`, error);
                }
            }
        }
        
        // All endpoints failed
        throw new Error(`All endpoints failed. Last error: ${lastError.message}`);
    }
    
    getNextEndpoint() {
        // Round-robin with failed endpoint avoidance
        let attempts = 0;
        while (attempts < this.endpoints.length) {
            const endpoint = this.endpoints[this.currentEndpointIndex];
            this.currentEndpointIndex = (this.currentEndpointIndex + 1) % this.endpoints.length;
            
            if (!this.failedEndpoints.has(endpoint)) {
                return endpoint;
            }
            
            attempts++;
        }
        
        // If all endpoints are marked as failed, clear the failed set and try again
        this.failedEndpoints.clear();
        return this.endpoints[0];
    }
    
    async callEndpoint(endpoint, prompt, data, options) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const requestOptions = {
            method: 'POST',
            body: formData,
            headers: this.config.requestHeaders,
            credentials: 'include',
            timeout: this.config.requestOptions.timeout
        };
        
        const response = await fetch(`${endpoint}/ask`, requestOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.text || 'Generation failed');
        }
        
        return result;
    }
    
    getCacheKey(prompt, data, options) {
        return btoa(JSON.stringify({ prompt, data, options }));
    }
}
```

### 3. Monitoring and Analytics

```javascript
class VisualizationAnalytics {
    constructor(config) {
        this.config = config;
        this.metrics = {
            requests: 0,
            successes: 0,
            failures: 0,
            totalResponseTime: 0,
            errors: []
        };
    }
    
    recordRequest(prompt, startTime) {
        this.metrics.requests++;
        
        return {
            recordSuccess: (responseTime) => {
                this.metrics.successes++;
                this.metrics.totalResponseTime += responseTime;
                this.sendMetrics('success', { prompt, responseTime });
            },
            
            recordFailure: (error, responseTime) => {
                this.metrics.failures++;
                this.metrics.errors.push({
                    prompt,
                    error: error.message,
                    timestamp: Date.now(),
                    responseTime
                });
                this.sendMetrics('failure', { prompt, error: error.message, responseTime });
            }
        };
    }
    
    sendMetrics(type, data) {
        if (this.config.analytics && this.config.analytics.endpoint) {
            fetch(this.config.analytics.endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type,
                    data,
                    timestamp: Date.now(),
                    userAgent: navigator.userAgent,
                    sessionId: this.getSessionId()
                })
            }).catch(error => {
                console.warn('Failed to send analytics:', error);
            });
        }
    }
    
    getMetrics() {
        const avgResponseTime = this.metrics.requests > 0 
            ? this.metrics.totalResponseTime / this.metrics.successes 
            : 0;
            
        return {
            ...this.metrics,
            successRate: this.metrics.requests > 0 
                ? this.metrics.successes / this.metrics.requests 
                : 0,
            averageResponseTime: avgResponseTime
        };
    }
    
    getSessionId() {
        if (!this.sessionId) {
            this.sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        }
        return this.sessionId;
    }
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Connection Issues

**Problem**: Cannot connect to LLM service
```
Error: Failed to fetch
```

**Solutions**:
```javascript
// Check if service is running
fetch('http://localhost:5008/')
  .then(response => console.log('Service is running'))
  .catch(error => console.log('Service is not accessible'));

// Verify CORS configuration
const config = {
    llmServiceURL: "http://localhost:5008/ask",
    requestOptions: {
        mode: 'cors',
        credentials: 'include'
    }
};
```

#### 2. Authentication Issues

**Problem**: SiteMinder authentication failures
```
Error: Authentication failed
```

**Solutions**:
```javascript
// Check SiteMinder session
fetch('/userinfo')
  .then(response => response.json())
  .then(data => console.log('User info:', data));

// Ensure credentials are included
const requestOptions = {
    method: 'POST',
    credentials: 'include',  // Important for SiteMinder
    body: formData
};
```

#### 3. Generation Issues

**Problem**: LLM fails to generate valid configuration
```
Error: No configuration was generated by the LLM
```

**Solutions**:
```javascript
// Try different models
const options = {
    model: 'gemini-1.5-flash',  // Try different model
    temperature: 0.1,           // Lower temperature for consistency
    maxTokens: 2048            // Increase token limit
};

// Improve prompt specificity
const betterPrompt = "Create a bar chart showing sales data by region with title 'Regional Sales Analysis' and blue color scheme";
```

#### 4. Performance Issues

**Problem**: Slow response times
```
Request timeout after 30 seconds
```

**Solutions**:
```javascript
// Increase timeout
const config = {
    requestOptions: {
        timeout: 60000  // 60 seconds
    }
};

// Use faster models
const options = {
    model: 'gemini-1.5-flash',  // Faster than GPT-4
    maxTokens: 1024            // Reduce token limit
};

// Implement caching
const cache = new Map();
const cacheKey = btoa(prompt + JSON.stringify(data));
if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
}
```

### Debugging Tools

```javascript
// Enable debug mode
const debugConfig = {
    debug: true,
    llmServiceURL: "http://localhost:5008/ask",
    onRequest: (request) => console.log('Request:', request),
    onResponse: (response) => console.log('Response:', response),
    onError: (error) => console.error('Error:', error)
};

// Network debugging
function debugNetworkCall(url, options) {
    console.log('Making request to:', url);
    console.log('Request options:', options);
    
    const startTime = Date.now();
    
    return fetch(url, options)
        .then(response => {
            const endTime = Date.now();
            console.log(`Request completed in ${endTime - startTime}ms`);
            console.log('Response status:', response.status);
            return response;
        })
        .catch(error => {
            const endTime = Date.now();
            console.error(`Request failed after ${endTime - startTime}ms:`, error);
            throw error;
        });
}
```

## Advanced Examples

### 1. Multi-Dataset Visualization

```javascript
async function createMultiDatasetVisualization() {
    const datasets = [
        { name: 'Sales', data: salesData },
        { name: 'Marketing', data: marketingData },
        { name: 'Support', data: supportData }
    ];
    
    const prompt = "Create a multi-panel dashboard showing trends for each dataset with shared time axis";
    
    // Generate configuration for combined visualization
    const formData = new FormData();
    formData.append('prompt', prompt);
    formData.append('datafile_contents', JSON.stringify({
        datasets: datasets
    }));
    formData.append('model', 'gpt-4o');
    
    const response = await fetch('http://localhost:5008/ask', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Create CanvasXpress with multi-dataset configuration
        new CanvasXpress(result.data, result.config, 'multiDatasetCanvas');
    }
}
```

### 2. Real-time Data Integration

```javascript
class RealTimeVisualization {
    constructor(apiUrl, containerId) {
        this.apiUrl = apiUrl;
        this.containerId = containerId;
        this.visualization = null;
        this.updateInterval = null;
    }
    
    async initialize(prompt, initialData) {
        // Create initial visualization
        const config = await this.generateConfig(prompt, initialData);
        this.visualization = new CanvasXpress(initialData, config, this.containerId);
        
        // Start real-time updates
        this.startRealTimeUpdates();
    }
    
    async generateConfig(prompt, data) {
        const formData = new FormData();
        formData.append('prompt', prompt);
        formData.append('datafile_contents', JSON.stringify(data));
        formData.append('config_only', 'true');  // Only return config
        
        const response = await fetch(`${this.apiUrl}/ask`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        return result.success ? result.config : null;
    }
    
    startRealTimeUpdates() {
        this.updateInterval = setInterval(async () => {
            try {
                // Fetch new data
                const newData = await this.fetchLatestData();
                
                // Update visualization
                this.visualization.updateData(newData);
                
            } catch (error) {
                console.error('Failed to update real-time data:', error);
            }
        }, 5000); // Update every 5 seconds
    }
    
    async fetchLatestData() {
        // Implement your data fetching logic
        const response = await fetch('/api/latest-data');
        return await response.json();
    }
    
    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Usage
const realTimeViz = new RealTimeVisualization('http://localhost:5008', 'realTimeCanvas');
realTimeViz.initialize(
    "Real-time line chart showing server metrics with automatic scaling",
    initialServerData
);
```

### 3. Custom Styling Integration

```javascript
async function createStyledVisualization(prompt, data, stylePreset) {
    const stylePrompts = {
        scientific: "Use scientific color scheme with clean typography and minimal design",
        corporate: "Apply corporate branding with company colors and professional styling",
        presentation: "Create presentation-ready visualization with large fonts and high contrast",
        publication: "Design for academic publication with grayscale compatibility"
    };
    
    const enhancedPrompt = `${prompt}. ${stylePrompts[stylePreset] || ''}`;
    
    const formData = new FormData();
    formData.append('prompt', enhancedPrompt);
    formData.append('datafile_contents', JSON.stringify(data));
    formData.append('model', 'gpt-4o');
    
    const response = await fetch('http://localhost:5008/ask', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
        // Apply additional styling if needed
        const config = result.config;
        
        // Add custom CSS classes
        config.customCSS = getCustomCSS(stylePreset);
        
        // Create visualization
        new CanvasXpress(result.data, config, 'styledCanvas');
    }
}

function getCustomCSS(preset) {
    const styles = {
        scientific: `
            .canvasxpress-container { font-family: 'Arial', sans-serif; }
            .canvasxpress-title { font-weight: bold; color: #333; }
        `,
        corporate: `
            .canvasxpress-container { font-family: 'Helvetica', sans-serif; }
            .canvasxpress-title { color: #0066cc; }
        `,
        // Add more presets as needed
    };
    
    return styles[preset] || '';
}
```

---

*This integration guide is maintained alongside the API documentation. For the latest updates and examples, please refer to the repository documentation.*