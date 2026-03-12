# FinChat - Financial Statement Chatbot

A full-stack application for analyzing financial statements with AI. The current runtime is a **hybrid deployment**:

- the **Streamlit app** handles the interactive UI and the live `FinChat` agent runtime
- the **FastAPI backend** manages session APIs, persistence, and document/session service orchestration

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Streamlit     │────▶│   FastAPI       │
│   UI + Agent    │     │   Session API   │
│   (port 8501)   │◀────│   (port 8000)   │
└─────────────────┘     └─────────────────┘
         │                        │
         ▼                        ▼
┌─────────────────┐     ┌─────────────────┐
│   OpenRouter    │     │   Persistence   │
│   AI API        │     │   (JSON files)  │
└─────────────────┘     └─────────────────┘
```

- **Streamlit app**: `localhost:8501`
- **Backend API**: `localhost:8000`
- **LLM**: OpenRouter API (OpenAI-compatible)
- **Storage**: JSON files in `data/sessions/` for persisted chat sessions

## Recent Enhancements

- ✅ **Unified Tools System**: All tools consolidated under `backend/finchat_backend/tools`
- ✅ **Centralized Tool Registry**: Single source of truth for tool discovery and registration
- ✅ **Tool Executor**: Uniform interface for executing any registered tool
- ✅ **Data Source Adapters**: Extensible Yahoo Finance integration with standardized result format
- ✅ **Financial Statements Tool**: Retrieve income statements, balance sheets, cash flow statements
- ✅ **Market Data Tool**: Real-time stock quotes, company information, historical price data
- ✅ **Comprehensive Test Suite**: 138 passing tests with full coverage

## Features

- 💬 Interactive chat interface with streaming responses
- 📄 Upload financial documents (PDF, HTML, TXT)
- 💾 **Persistent sessions** - chat history survives page refresh and app restart
- 🎯 Automatic financial analysis
- 🌐 Multi-session support with conversation switching
- 📊 Real-time document search
- 📈 **Real-time market data** - stock prices, company information, historical charts
- 💰 **Financial statements** - income statements, balance sheets, cash flow statements
- 🔧 **Extensible tool system** - unified tool registry and executor for adding new capabilities

## Prerequisites

- Python 3.10+
- OpenRouter API key from [openrouter.ai](https://openrouter.ai)
- Git (optional)

## Quick Start

### 1. Clone and Setup

```bash
cd /path/to/finchat

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies (Streamlit + Backend)
pip install -r requirements.txt 
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
OPENROUTER_API_KEY=sk-or-your-api-key-here
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
API_BASE_URL=http://localhost:8000
DATA_DIR=./data
LOG_LEVEL=INFO
```

Notes:

- `OPENROUTER_API_KEY` is required by the Streamlit app because the live `FinChat` runtime is initialized there.
- `API_BASE_URL` tells Streamlit where to find the backend session API.
- `DATA_DIR` is shared by the backend for persisted sessions and downloaded filings.
- If you run the backend from `backend/`, you can also place the same variables in `backend/.env`. In production, exported environment variables are preferred over relying on `.env`.

### 3. Start the Backend

From the project root:

```bash
uvicorn finchat_backend.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:

```bash
cd backend
python run.py
```

The API will be available at:
- **API docs**: http://localhost:8000/api/docs
- **Health check**: http://localhost:8000/api/health

### 4. Start the Streamlit App

In a **new terminal** (keeping the backend running):

```bash
streamlit run app.py
```

The app will open at **http://localhost:8501**

## Detailed Usage

### First Run

1. When you first open the app, it will automatically create a new chat session
2. The backend loads any previously saved sessions from `data/sessions/`
3. The Streamlit app initializes the in-process `FinChat` runtime from environment variables
4. You'll see the chat interface ready to use

### Chat Sessions

- **New Chat**: Click "➕ New Chat" in the left panel to start a fresh conversation
- **Switch**: Click on any previous session in the history to load it
- **Auto-save**: Every message exchange is automatically saved to disk
- **Delete**: Remove unwanted sessions from the history panel

### Working with Documents

1. Go to the "Upload" section in the left panel
2. Choose "Upload File"
3. Select a PDF, HTML, or TXT file
4. Click "📥 Load Document"

### Chat Interface

- Type your message in the input box at the bottom
- Press **Enter** to send, **Shift+Enter** for newline
- The assistant streams responses in real-time
- Scroll up to see conversation history

## API Endpoints (for developers)

### Sessions
- `GET /api/v1/sessions` - List all in-memory sessions
- `GET /api/v1/persisted-sessions` - List all saved sessions on disk
- `POST /api/v1/sessions` - Create a new session
- `GET /api/v1/sessions/{id}` - Get session details including messages
- `POST /api/v1/sessions/{id}/persist` - Save session to disk
- `POST /api/v1/persisted-sessions/{id}/load` - Load saved session into memory
- `DELETE /api/v1/sessions/{id}` - Delete session
- `DELETE /api/v1/persisted-sessions/{id}` - Delete from disk

### Chat
- `POST /api/v1/chat` - Send a message
  ```json
  {
    "session_id": "uuid-here",
    "message": "Your question"
  }
  ```

### Files
- `POST /api/v1/upload` - Upload document (multipart)
- `POST /api/v1/sec-download` - Download and load an SEC filing
- `DELETE /api/v1/sessions/{id}/document` - Clear document

## Configuration

### Shared / Streamlit Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key used by the Streamlit runtime |
| `OPENROUTER_MODEL` | No | `stepfun/step-3.5-flash:free` | Model to use |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | API base URL |
| `DATA_DIR` | No | `./data` | Directory for SEC filings and session data |
| `MAX_DOCUMENT_SIZE` | No | `100000` | Max characters per document |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `API_BASE_URL` | No | `http://localhost:8000` | Backend session API URL used by Streamlit |

### Backend-only Runtime Notes

The backend also reads `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` so it can build compatible session-side services. In production, set the same values for both processes.

### Data Sources

The application supports external data sources through a unified adapter interface:

- **Yahoo Finance**: Real-time stock prices, company info, historical data, and financial statements
  - No additional configuration required
  - Uses the `yfinance` Python package
  - Adapter: `agent_service.data_sources.yahoo_adapter.YahooFinanceAdapter`

### Tool Registry

Tools are registered through a centralized system:

- Location: `agent_service.tools.tool_registry`
- Global registry: `registry` singleton
- Used for dynamic tool discovery and execution by agents
- Extensible: Register custom tools with `registry.register(name, func, description, tool_type)`

### Available Tools

**Document Tools:**
- `search_document` (`SearchTool`) - Search within loaded documents
- `analyze_financials` (`FinAnalysisTool`) - Generate financial analysis using LLM

**Data Tools:**
- `get_financial_statements` (`FinancialStatementsTool`) - Retrieve income statement, balance sheet, cash flow
- `get_market_data` (`MarketDataTool`) - Get real-time stock quotes, company info, historical data

### Tool Executor

The `ToolExecutor` (`agent_service.agent.executor.ToolExecutor`) provides a unified interface for executing registered tools:

- Initialize with a registry: `executor = ToolExecutor(registry)`
- Execute tools: `result = executor.execute("tool_name", param1=value1, param2=value2)`
- Safe execution returns dictionary: `result = executor.execute_safe("tool_name", **params)`
- List available tools: `tools = executor.list_available_tools()`
- Get tool info: `info = executor.get_tool_info("tool_name")`

The executor handles errors, parameter validation, and result standardization automatically.

## Troubleshooting

### "OPENROUTER_API_KEY not set"
- Ensure `.env` exists in the project root, or export the variable before starting both services
- Verify the API key is correct and has credits
- Restart both backend and Streamlit after updating environment variables

### Backend won't start
- Check Python version: `python --version` (should be 3.10+)
- Reinstall all dependencies: `pip install -r requirements.txt`
- Check if port 8000 is in use: `lsof -i :8000`

### Frontend can't connect to backend
- Ensure backend is running: `curl http://localhost:8000/api/health`
- Check `API_BASE_URL` in root `.env` or environment
- Verify CORS settings in `backend/finchat_backend/main.py`

### Session not persisting
- Ensure `DATA_DIR` is writable
- Check `data/sessions/` directory exists
- Look at backend logs for errors

### "No module named 'finchat'"
- Ensure you're running commands from the project root
- The backend uses `agent_service` package from `backend/finchat_backend/`
- Reinstall dependencies if imports are still missing: `pip install -r requirements.txt`

### `sec-edgar-downloader` / `pyrate-limiter` errors
- Install the pinned root dependencies: `pip install -r requirements.txt`
- This project expects `pyrate-limiter==3.1.0` for SEC download compatibility

## Development

### Adding New Features

1. **Backend API / services**: Modify files in `backend/finchat_backend/`
2. **Streamlit UI**: Modify `app.py`
3. **New Data Source**: Subclass `DataSourceAdapter` in `backend/finchat_backend/tools/data_sources/` and register
4. **New Tool**: Subclass `Tool` in `backend/finchat_backend/tools/` - auto-registered on import
5. **Agent logic**: Modify `backend/finchat_backend/agent_service/agent/agent.py`

### Tools Architecture

The unified tool system centers on:

- **Tool Registry** (`tools/tool_registry.py`): Central repository for all available tools
- **Tool Executor** (`tools/executor.py`): Executes tools by name with unified error handling
- **Auto-registration**: Tools are auto-discovered and registered when `finchat_backend.tools` is imported
- **Agent Integration**: The `FinChat` agent accepts an optional `executor` parameter and will use it if provided (see `core/factories/agent_factory.py`)

### Testing

```bash
# Test backend API
curl http://localhost:8000/api/health

# Run all tests (138 tests as of latest update)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run backend tests
pytest tests/backend/ -v
```

## Deployment

### Local Development
- Follow "Quick Start" above

### Production (Single Server)

Run both processes separately and give them the same environment variables:

1. **Backend API**
   ```bash
   uvicorn finchat_backend.main:app --app-dir backend --host 0.0.0.0 --port 8000
   ```
2. **Streamlit app**
   ```bash
   streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
   ```
3. **Reverse proxy**
   ```text
   https://yourdomain.com/      -> http://127.0.0.1:8501
   https://yourdomain.com/api/  -> http://127.0.0.1:8000/api/
   ```
4. **Process supervision**
   Use `systemd`, `supervisord`, Docker, or another process manager to keep both services alive.

Recommended production environment variables:

```bash
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
API_BASE_URL=https://yourdomain.com
DATA_DIR=/var/lib/finchat/data
LOG_LEVEL=INFO
```

### Docker Deployment

Use two containers or one compose stack: one for the backend and one for Streamlit.

```dockerfile
# Backend
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY backend ./backend
COPY src ./src
COPY data ./data
CMD ["uvicorn", "finchat_backend.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Streamlit
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py ./
COPY src ./src
COPY data ./data
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Cloud Platforms

- **Render**: Deploy both services as separate Web Services
- **Railway**: Similar deployment with proper service linking
- **Fly.io**: Use volumes for persistent storage
- **AWS/GCP/Azure**: Use ECS/Cloud Run/App Services with persistent disks

**Note**: The current persistence uses local JSON files. For multi-instance deployments, replace file-backed sessions with a shared store such as PostgreSQL, Redis, or object storage.

## Environment-specific Notes

### Running on China Mainland
Use Tsinghua PyPI mirror for faster installs:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

OpenRouter may require a VPN or use a China-compatible LLM provider (modify `OPENROUTER_BASE_URL`).

### Security Considerations

- The backend allows any origin by default (`allow_origins=["*"]`). Restrict in production.
- API keys are stored in environment variables or `.env` files - never commit them
- SEC download tool includes an `email` parameter - set a real email in production
- Consider adding authentication/rate limiting for production use

## FAQ

**Q: How do I change the AI model?**
A: Set `OPENROUTER_MODEL` in the backend `.env`. See OpenRouter for available models.

**Q: Where are chat sessions stored?**
A: In `data/sessions/*.json`. Each session is a JSON file with messages, metadata, and document source.

**Q: Can I share a session between users?**
A: Sessions are stored per server instance. For multi-user support, add user authentication and namespace the session IDs.

**Q: Does it work offline?**
A: No - requires OpenRouter API for chat responses. SEC downloads and document uploads work.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes
4. Submit a pull request

## License

MIT
