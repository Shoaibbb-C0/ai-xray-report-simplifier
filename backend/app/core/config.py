"""Application configuration settings."""

import os
from typing import List


class Settings:
    """Core settings loaded from environment variables with safe defaults."""

    PROJECT_NAME: str = "AI X-Ray Patient Support API"
    SERVICE_NAME: str = "ai-xray-backend"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Server host and port configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Allowed CORS origins for frontend integration
    CORS_ORIGINS: List[str] = [origin.strip() for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",") if origin.strip() and origin.strip() != "*"]


settings = Settings()
