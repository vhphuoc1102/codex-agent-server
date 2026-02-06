import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Codex CLI path
    codex_path: str = "codex"

    # Client identification
    client_name: str = "codex-bridge-server"
    client_title: str = "Codex Bridge Server"
    client_version: str = "0.1.0"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Timeouts (in seconds)
    request_timeout: float = 300.0
    initialization_timeout: float = 30.0

    # Logging
    log_level: str = "INFO"

    class Config:
        env_prefix = "CODEX_"
        case_sensitive = False


settings = Settings()
