# FinChat Backend API

FastAPI backend that powers the Streamlit frontend for financial statement analysis.

## Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment variables:

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set your OpenRouter API key:

```bash
OPENROUTER_API_KEY=sk-or-your-api-key-here
```

Optional: Set the model (default: `stepfun/step-3.5-flash:free`)

```bash
OPENROUTER_MODEL=stepfun/step-3.5-flash:free
```

## Running the Server

### Development (with auto-reload)

```bash
uvicorn finchat_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the provided script:

```bash
python run.py
```

### Production

```bash
uvicorn finchat_backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at:
- **API docs**: http://localhost:8000/api/docs
- **Health check**: http://localhost:8000/api/health
- **API base**: http://localhost:8000/api/v1/

## API Endpoints

### Chat
- `POST /api/v1/chat` - Send a message and get a response
- `GET /api/v1/sessions/{session_id}/history` - Get session message history
- `DELETE /api/v1/sessions/{session_id}/history` - Clear session history

### Sessions
- `GET /api/v1/sessions` - List all active sessions (in-memory + auto-loaded persisted)
- `GET /api/v1/persisted-sessions` - List all saved sessions on disk
- `POST /api/v1/sessions` - Create a new session
- `GET /api/v1/sessions/{session_id}` - Get session details (messages, document)
- `DELETE /api/v1/sessions/{session_id}` - Delete session
- `POST /api/v1/sessions/{session_id}/persist` - Save session to disk
- `POST /api/v1/persisted-sessions/{session_id}/load` - Load saved session into memory
- `DELETE /api/v1/persisted-sessions/{session_id}` - Delete saved session
- `POST /api/v1/sessions/{session_id}/reset` - Reset session (clear history + document)

### Files
- `POST /api/v1/upload` - Upload document (multipart/form-data)
- `DELETE /api/v1/sessions/{session_id}/document` - Clear document from session

## Frontend Integration

This backend is designed to work with the Streamlit frontend (`app.py` in the project root).

**Frontend configuration**:
- The Streamlit app calls this backend at `http://localhost:8000` by default
- To override, set `API_BASE_URL` environment variable in the frontend

### Auto-loading Persisted Sessions

On startup, the AgentManager automatically loads all sessions from `data/sessions/` into memory. This means:
- Sessions persist across server restarts
- The `GET /api/v1/sessions` endpoint returns both in-memory and auto-loaded sessions
- Each session's `persisted` field indicates if it's saved to disk

## Session Persistence

Sessions are saved as JSON files in `DATA_DIR/sessions/` (default: `./data/sessions/`).

Each session file contains:
```json
{
  "id": "uuid",
  "title": "First message title...",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
  ],
  "doc_source": "Uploaded: file.pdf",
  "timestamp": "2026-03-11T...",
  "saved_at": "2026-03-11T...",
  "message_count": 2
}
```

**Note**: Document content is NOT persisted for security/storage reasons. Only the document source reference is saved. Users must reload documents after restoring a session.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key (starts with `sk-or-`) |
| `OPENROUTER_MODEL` | No | `stepfun/step-3.5-flash:free` | Model identifier on OpenRouter |
| `OPENROUTER_BASE_URL` | No | `https://openrouter.ai/api/v1` | API endpoint |
| `DATA_DIR` | No | `./data` | Directory for SEC filings and session data |
| `MAX_DOCUMENT_SIZE` | No | `100000` | Max characters per document |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `APP_NAME` | No | `Financial Chatbot` | Application name |
| `DEBUG` | No | `false` | Enable debug mode |

## Project Structure

```
backend/
├── finchat_backend/
│   ├── main.py              # FastAPI application entry
│   ├── core/
│   │   ├── agent_manager.py  # Manages agents + persistence
│   │   └── persistence.py    # JSON file session storage
│   └── api/
│       └── v1/
│           ├── chat.py       # Chat endpoints
│           ├── sessions.py   # Session management + persistence
│           └── files.py      # File upload/download
├── src/finchat/             # Core agent framework
│   ├── agent/
│   ├── config.py
│   ├── models.py
│   └── ...
├── data/
│   ├── sessions/            # JSON session files (auto-created)
│   └── sec/                 # SEC filings cache (auto-created)
├── .env.example
├── requirements.txt
├── run.py
└── README.md
```

## Troubleshooting

### "No module named 'finchat'"
- Ensure `src/` directory is in the Python path
- Run from the `backend/` directory (not inside `finchat_backend/`)
- The backend adds `ROOT_DIR/src` to `sys.path` automatically

### "OPENROUTER_API_KEY not set"
- Check that `.env` exists in `backend/` directory
- Use absolute path if running from different location

### Port 8000 already in use
```bash
lsof -i :8000  # Find process
kill <PID>     # Kill it
```

### OpenAI client initialization error: "unexpected keyword argument 'proxies'"
- This is caused by httpx 0.28+ incompatibility
- Ensure `httpx==0.27.0` is installed
- The `requirements.txt` is pinned to avoid this issue

## Development Tips

### Hot Reload
Start uvicorn with `--reload` for automatic code reloading on changes.

### API Testing
- Interactive docs: http://localhost:8000/api/docs
- Or use `curl`/Postman to test endpoints

### Logging
Logs are written to stdout. For debugging, set `LOG_LEVEL=DEBUG` in `.env`.

### Session Data
Persisted sessions are in `data/sessions/*.json`. You can manually edit or delete these files.

## Performance Notes

- Agent instances are kept in memory - fast for active sessions
- Sessions auto-load from disk on backend startup (may take time if many sessions)
- SEC downloads are rate-limited to respect Edgar's policies
- Large documents are truncated to `MAX_DOCUMENT_SIZE` (default 100k chars)

## Deployment Considerations

For multi-user or production deployments:

1. **Session Storage**: Replace JSON files with Redis or PostgreSQL for better concurrency
2. **CORS**: Update `CORSMiddleware` in `main.py` to restrict origins
3. **Authentication**: Add API key or OAuth middleware
4. **Rate Limiting**: Implement per-user/IP rate limits
5. **Monitoring**: Add metrics endpoint and logging aggregation
6. **HTTPS**: Use reverse proxy (nginx) with SSL termination
7. **Process Manager**: Use systemd, supervisor, or pm2 for auto-restart

See main README.md for complete deployment guide.
