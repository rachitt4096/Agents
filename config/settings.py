"""
Configuration settings for Action-Oriented Multi-Agent System
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    GROQ_API_KEY: str
    COORDINATOR_MODEL: str = "llama-3.1-70b-versatile"
    WORKER_MODEL: str = "llama-3.1-8b-instant"
    
    # Streamlit
    STREAMLIT_PORT: int = 8501
    
    # Execution Settings
    MAX_RETRIES: int = 3
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 2000
    TIMEOUT_SECONDS: int = 300  # 5 minutes for long tasks
    
    # Action Execution
    ENABLE_CODE_EXECUTION: bool = True
    ENABLE_FILE_OPERATIONS: bool = True
    ENABLE_SHELL_COMMANDS: bool = True
    WORKSPACE_DIR: str = "./workspace"
    MAX_FILE_SIZE_MB: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/orchestrator.log"
    RUNTIME_LOG: str = "logs/runtime.log"
    
    # Security
    ALLOWED_COMMANDS: list = [
        "ls", "cat", "echo", "pwd", "whoami", "date",
        "python", "pip", "git", "curl", "wget"
    ]
    BLOCKED_COMMANDS: list = [
        "rm -rf", "mkfs", "dd", "fork", ":()", "shutdown", "reboot"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)