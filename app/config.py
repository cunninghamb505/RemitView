"""Application settings."""
import os
from pathlib import Path


class Settings:
    HOST: str = os.getenv("EDI_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("EDI_PORT", "8000"))
    DB_PATH: str = os.getenv("EDI_DB_PATH", str(Path(__file__).parent.parent / "edi835.db"))
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB


settings = Settings()
