"""
FinChat FastAPI Backend

Provides REST API for the React frontend to interact with the FinChat agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from finchat_backend.core.bootstrap import ROOT_DIR, ensure_project_path

ensure_project_path()

# Import API routers
from finchat_backend.api.v1 import router as api_v1_router

# Create FastAPI app
app = FastAPI(
    title="FinChat API",
    description="Financial Statement Chatbot API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_v1_router, prefix="/api/v1")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "finchat-backend"}

if __name__ == "__main__":
    uvicorn.run("finchat_backend.main:app", host="0.0.0.0", port=8000, reload=True)
