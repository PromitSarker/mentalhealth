"""Main FastAPI application for AI Therapy Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

from app.routers import chat, audio, reports


# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title="AI Therapy Platform",
    description="AI therapy assistant with risk detection, scoring, and audio",
    version="1.0.0",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(chat.router)
app.include_router(audio.router)
app.include_router(reports.router)


@app.get("/")
async def root() -> dict:
    """Root endpoint with API information."""
    return {
        "service": "AI Therapy Platform",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/ai/chat/interact",
            "chat_clear_session": "/ai/chat/session/{session_id} [DELETE]",
            "audio_stt": "/ai/audio/stt",
            "audio_tts": "/ai/audio/tts",
            "reports": "/ai/report/generate",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),
        port=int(os.getenv("SERVER_PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true",
    )
