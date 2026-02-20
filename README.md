# AI Chatbot Backend API

A production-ready Python backend API for an AI-powered chatbot with tool calling capabilities and persistent memory for multi-turn conversations. Built with FastAPI, LangChain, and OpenAI, designed for customer support and assistant applications.

## Features

- 🤖 **AI-Powered Conversations**: Leverages OpenAI GPT-4 with tool calling support
- 🛠️ **Tool Integration**: Built-in tools for calculations, web search, and weather information
- 💾 **Persistent Memory**: SQLite-based conversation history with session management
- 🔄 **Multi-Turn Support**: Maintains context across conversation turns
- 📡 **Streaming Responses**: Server-Sent Events (SSE) support for real-time responses
- 🔒 **Security**: Optional API key authentication
- 🐳 **Docker Support**: Containerized deployment ready
- ✅ **Tested**: Comprehensive unit tests with pytest

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP/SSE
       ▼
┌─────────────────────────────────┐
│      FastAPI Application        │
│  ┌───────────────────────────┐ │
│  │   API Endpoints            │ │
│  │  /chat, /sessions, /tools  │ │
│  └───────────┬─────────────────┘ │
│              │                    │
│  ┌───────────▼─────────────────┐ │
│  │   LangChain Agent           │ │
│  │   (Tool Calling Executor)   │ │
│  └───────────┬─────────────────┘ │
│              │                    │
│  ┌───────────▼─────────────────┐ │
│  │   Tools                     │ │
│  │  Calculator, Web Search,    │ │
│  │  Weather                    │ │
│  └─────────────────────────────┘ │
│              │                    │
│  ┌───────────▼─────────────────┐ │
│  │   Memory (SQLite)           │ │
│  │   Conversation History      │ │
│  └─────────────────────────────┘ │
└─────────────────────────────────┘
       │
       ▼
┌─────────────┐
│   OpenAI    │
│   GPT-4     │
└─────────────┘
```

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd AI-Chatbot-Backend-API-1
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

5. **Create database directory:**
   ```bash
   mkdir -p db
   ```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `OPENAI_TEMPERATURE` | LLM temperature | `0.7` |
| `OPENAI_MAX_TOKENS` | Maximum tokens per response | `1000` |
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `API_KEY` | API key for authentication | - |
| `ENABLE_AUTH` | Enable API key authentication | `false` |
| `AGENT_MAX_ITERATIONS` | Maximum agent iterations | `15` |
| `MEMORY_TYPE` | Memory storage type | `sqlite` |
| `SQLITE_DB_PATH` | SQLite database path | `db/conversations.db` |
| `ENABLE_WEB_SEARCH` | Enable web search tool | `true` |
| `ENABLE_CALCULATOR` | Enable calculator tool | `true` |
| `ENABLE_WEATHER` | Enable weather tool | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Docker Deployment

### Build the Docker Image

```bash
docker build -t ai-chatbot-api .
```

### Run the Container

```bash
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/db:/app/db \
  --name chatbot-api \
  ai-chatbot-api
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./db:/app/db
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Support

- Telegram: https://t.me/az_tekDev
- Twitter: https://x.com/az_tekDev
