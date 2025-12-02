"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./wavy_nutrition.db"
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = "openai"  # openai, azure, or bedrock
    OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""
    
    # Session & Security
    SESSION_SECRET: str = "change-me-in-production"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Redis (optional)
    REDIS_URL: str = ""
    
    # LLM Settings
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    LLM_RETRY_ATTEMPTS: int = 3
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
