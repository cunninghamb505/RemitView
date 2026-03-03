"""Application settings."""
import os
import sys
from pathlib import Path

APP_NAME = "RemitView"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Brandon Cunningham"


def _is_frozen():
    """Check if running as a PyInstaller bundle."""
    return getattr(sys, 'frozen', False)


def _get_default_db_path():
    """Get the default database path based on run mode."""
    if _is_frozen():
        # Exe mode: store DB in user's home directory
        db_dir = Path.home() / "RemitView"
        db_dir.mkdir(exist_ok=True)
        return str(db_dir / "remitview.db")
    return str(Path(__file__).parent.parent / "edi835.db")


def _get_base_dir():
    """Get the base directory for the application."""
    if _is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).parent.parent


class Settings:
    HOST: str = os.getenv("EDI_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("EDI_PORT", "8000"))
    DB_PATH: str = os.getenv("EDI_DB_PATH", _get_default_db_path())
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    IS_FROZEN: bool = _is_frozen()
    BASE_DIR: Path = _get_base_dir()


settings = Settings()
