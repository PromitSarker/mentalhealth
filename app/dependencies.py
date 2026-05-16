"""Application configuration and dependencies."""

import os


class Settings:
    """Application settings."""
    
    def __init__(self):
        self.app_name = "AI Therapy Platform"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.server_host = os.getenv("SERVER_HOST", "0.0.0.0")
        self.server_port = int(os.getenv("SERVER_PORT", "8000"))
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
