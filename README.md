# Codex Agent Server

A REST API bridge server for the Codex CLI, providing HTTP endpoints that translate to JSON-RPC calls for AI agent interactions.

## Features

- REST API wrapper for Codex CLI app-server
- Docker support with configurable model providers
- Support for custom API endpoints (OpenAI-compatible)
- Thread management (create, resume, fork, read)
- Turn-based conversation handling
- Skills management

## Quick Start

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 2. Configure Environment Variables

Edit `.env` file:

```env
# Server Port (external)
CODEX_SERVER_PORT=8000

# Codex Model Configuration
CODEX_MODEL_PROVIDER=cliproxyapi
CODEX_MODEL=gpt-5-codex
CODEX_MODEL_REASONING_EFFORT=high
CODEX_API_BASE_URL=http://host.docker.internal:8317/v1

# Codex Authentication
CODEX_API_KEY=sk-your-api-key-here
```

### 3. Run with Docker

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### 4. Verify

```bash
curl http://localhost:8000/health
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEX_SERVER_PORT` | External port mapping | `8000` |
| `CODEX_MODEL_PROVIDER` | Model provider name | `cliproxyapi` |
| `CODEX_MODEL` | Model to use | `gpt-5-codex` |
| `CODEX_MODEL_REASONING_EFFORT` | Reasoning effort level | `high` |
| `CODEX_API_BASE_URL` | API endpoint URL | `http://host.docker.internal:8317/v1` |
| `CODEX_API_KEY` | API key for authentication | - |
| `CODEX_CLIENT_NAME` | Client identifier | `codex-bridge-server` |
| `CODEX_LOG_LEVEL` | Logging level | `INFO` |
| `CODEX_REQUEST_TIMEOUT` | Request timeout (seconds) | `300` |

### Using with Different Providers

#### OpenAI Direct

```env
CODEX_MODEL_PROVIDER=openai
CODEX_MODEL=gpt-4
CODEX_API_BASE_URL=https://api.openai.com/v1
CODEX_API_KEY=sk-your-openai-key
```

#### Custom Proxy (e.g., LiteLLM, OpenRouter)

```env
CODEX_MODEL_PROVIDER=cliproxyapi
CODEX_MODEL=gpt-5-codex
CODEX_API_BASE_URL=http://host.docker.internal:8317/v1
CODEX_API_KEY=sk-dummy
```

## API Reference

### Health Check

```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Thread Operations

#### Create Thread

```bash
POST /api/thread/start
```

**Request:**
```json
{
  "cwd": "/workspace",
  "approvalPolicy": "never"
}
```

**Response:**
```json
{
  "thread": {
    "id": "thread_abc123",
    "preview": "",
    "createdAt": 1234567890
  }
}
```

#### Resume Thread

```bash
POST /api/thread/resume
```

**Request:**
```json
{
  "threadId": "thread_abc123"
}
```

#### Read Thread

```bash
POST /api/thread/read
```

**Request:**
```json
{
  "threadId": "thread_abc123",
  "includeTurns": true
}
```

#### Fork Thread

```bash
POST /api/thread/fork
```

**Request:**
```json
{
  "threadId": "thread_abc123"
}
```

### Turn Operations

#### Start Turn (Send Message)

```bash
POST /api/turn/start
```

**Request:**
```json
{
  "threadId": "thread_abc123",
  "input": [
    {
      "type": "text",
      "text": "Hello, can you help me write a Python function?"
    }
  ]
}
```

**Response:**
```json
{
  "turn": {
    "id": "turn_xyz789",
    "status": "completed",
    "items": [...]
  }
}
```

### Skills Operations

#### List Skills

```bash
POST /api/skills/list
```

**Request:**
```json
{}
```

#### Enable/Disable Skill

```bash
POST /api/skills/config/write
```

**Request:**
```json
{
  "path": "/path/to/skill",
  "enabled": true
}
```

## Examples

### Complete Conversation Flow

```bash
# 1. Create a new thread
THREAD_ID=$(curl -s -X POST http://localhost:8000/api/thread/start \
  -H "Content-Type: application/json" \
  -d '{"cwd": "/workspace"}' | jq -r '.thread.id')

echo "Thread ID: $THREAD_ID"

# 2. Send a message
curl -X POST http://localhost:8000/api/turn/start \
  -H "Content-Type: application/json" \
  -d "{
    \"threadId\": \"$THREAD_ID\",
    \"input\": [{
      \"type\": \"text\",
      \"text\": \"Write a hello world program in Python\"
    }]
  }"

# 3. Continue the conversation
curl -X POST http://localhost:8000/api/turn/start \
  -H "Content-Type: application/json" \
  -d "{
    \"threadId\": \"$THREAD_ID\",
    \"input\": [{
      \"type\": \"text\",
      \"text\": \"Now add a function to greet a specific name\"
    }]
  }"

# 4. Read thread history
curl -X POST http://localhost:8000/api/thread/read \
  -H "Content-Type: application/json" \
  -d "{
    \"threadId\": \"$THREAD_ID\",
    \"includeTurns\": true
  }"
```

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Create thread
response = requests.post(f"{BASE_URL}/api/thread/start", json={
    "cwd": "/workspace"
})
thread_id = response.json()["thread"]["id"]
print(f"Created thread: {thread_id}")

# Send message
response = requests.post(f"{BASE_URL}/api/turn/start", json={
    "threadId": thread_id,
    "input": [{"type": "text", "text": "Hello, what can you do?"}]
})
turn = response.json()["turn"]
print(f"Turn status: {turn['status']}")
print(f"Response items: {turn['items']}")
```

### JavaScript/Node.js Example

```javascript
const BASE_URL = 'http://localhost:8000';

async function chat(message) {
  // Create thread
  const threadRes = await fetch(`${BASE_URL}/api/thread/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ cwd: '/workspace' })
  });
  const { thread } = await threadRes.json();

  // Send message
  const turnRes = await fetch(`${BASE_URL}/api/turn/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      threadId: thread.id,
      input: [{ type: 'text', text: message }]
    })
  });
  const { turn } = await turnRes.json();

  return turn;
}

// Usage
chat('Write a function to calculate factorial').then(console.log);
```

## Troubleshooting

### Port Already in Use

```bash
# Change port in .env
CODEX_SERVER_PORT=8001

# Restart
docker compose down && docker compose up -d
```

### Cannot Connect to Host API

If your API proxy runs on the host machine:
- Use `host.docker.internal` instead of `localhost` or `127.0.0.1`
- The `extra_hosts` setting in docker-compose.yml handles this for Linux

### View Container Logs

```bash
docker compose logs -f codex-agent-server
```

### Check Generated Config

```bash
docker compose exec codex-agent-server cat /root/.codex/config.toml
docker compose exec codex-agent-server cat /root/.codex/auth.json
```

### Reset Data

```bash
docker compose down -v  # Removes volumes
docker compose up -d
```

## Development

### Run Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export CODEX_PATH=codex
export PYTHONPATH=.

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

MIT
