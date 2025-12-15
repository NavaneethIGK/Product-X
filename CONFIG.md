# OpenAI API Key Configuration

The Supply Chain AI Copilot now supports multiple flexible ways to configure the OpenAI API key:

## Configuration Methods (in priority order)

### 1. Environment Variable (Highest Priority)
Set the `OPENAI_API_KEY` environment variable before running the backend:

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-api-key-here"
python copilot_backend.py
```

**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY=sk-proj-your-api-key-here
python copilot_backend.py
```

**Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-proj-your-api-key-here"
python copilot_backend.py
```

### 2. .env File
Create a `.env` file in the project root directory with:
```
OPENAI_API_KEY=sk-proj-your-api-key-here
```

The application will automatically load this when starting.

### 3. config.json File
Create a `config.json` file in the project root directory with:
```json
{
  "openai_api_key": "sk-proj-your-api-key-here"
}
```

### 4. Runtime API Configuration (via HTTP endpoint)
Configure the API key dynamically while the server is running:

```bash
curl -X POST http://localhost:8000/config/openai \
  -H "Content-Type: application/json" \
  -d '{"openai_api_key": "sk-proj-your-api-key-here"}'
```

**Response:**
```json
{
  "message": "✅ OpenAI API key configured successfully",
  "openai_configured": true
}
```

## Checking Configuration Status

Check if OpenAI is properly configured:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-12-10T10:30:00.123456",
  "openai_configured": true
}
```

Get detailed configuration info:

```bash
curl http://localhost:8000/config
```

**Response:**
```json
{
  "openai_configured": true,
  "api_key_length": 48,
  "api_key_preview": "sk-proj-8O3-5a1drW...dHJQA"
}
```

## Security Notes

⚠️ **Important Security Considerations:**
- Never commit `.env` or `config.json` files to version control
- Avoid hardcoding API keys in your code
- Use environment variables for production deployments
- The API key preview only shows first 20 and last 4 characters for security
- The `/config/openai` endpoint should be protected in production

## Example Workflows

### Development Workflow
```bash
# Option 1: Use .env file (easiest for local development)
echo "OPENAI_API_KEY=sk-proj-your-key" > .env
python copilot_backend.py

# Option 2: Use environment variable
$env:OPENAI_API_KEY="sk-proj-your-key"
python copilot_backend.py
```

### Production Workflow (Ubuntu/Docker)
```bash
# Set environment variable and run
export OPENAI_API_KEY="sk-proj-your-key"
pm2 start ecosystem.config.js

# Or use .env file for PM2
pm2 start ecosystem.config.js --env production
```

### Testing Configuration
```bash
# Verify the configuration is loaded
curl http://localhost:8000/config

# Test a query with OpenAI enabled
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Which routes have most delays?"}'
```

## Troubleshooting

**"OpenAI API Key not configured" message**
- Check if OPENAI_API_KEY environment variable is set
- Verify `.env` or `config.json` exists in the project root
- Use `/config` endpoint to check current status

**"Invalid API key" error when making requests**
- Verify the key is correct (starts with `sk-proj-`)
- Check if the key has necessary permissions
- Ensure the key hasn't expired

**API key not persisting after server restart**
- Use `.env` or `config.json` file for persistent configuration
- Environment variables are reset when terminal closes
- For production, use PM2 with ecosystem config or system environment variables
