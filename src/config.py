"""Configuration management for the AI Chatbot Backend API."""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_title: str = "AI Chatbot Backend API"
    api_version: str = "1.0.0"
    api_description: str = "AI support backend with tool calling and persistent memory"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # Security
    api_key: Optional[str] = None
    enable_auth: bool = False
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 1000
    
    # LangChain Configuration
    agent_verbose: bool = False
    agent_max_iterations: int = 15
    agent_max_execution_time: Optional[int] = None
    
    # Memory Configuration
    memory_type: str = "sqlite"  # sqlite or redis
    sqlite_db_path: str = "db/conversations.db"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    memory_ttl: int = 86400  # 24 hours in seconds
    
    # Tool Configuration
    enable_web_search: bool = True
    enable_calculator: bool = True
    enable_weather: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
# Note: Validation happens lazily to allow imports without env vars set
settings = Settings()

def validate_settings():
    """Validate required settings. Call this before starting the server."""
    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your .env file or environment."
        )
