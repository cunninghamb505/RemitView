"""File watcher service for auto-importing ERA files from a directory."""
import os
import threading
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.services import file_service
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)

_observer = None
_watch_thread = None


class ERAFileHandler(FileSystemEventHandler):
    """Handles new EDI/835 files appearing in the watched directory."""

    VALID_EXTENSIONS = {".edi", ".835", ".txt", ".x12"}

    def on_created(self, event):
        if event.is_directory:
            return
        ext = Path(event.src_path).suffix.lower()
        if ext not in self.VALID_EXTENSIONS:
            return

        logger.info(f"New ERA file detected: {event.src_path}")
        try:
            with open(event.src_path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
            if "ISA" not in raw[:100]:
                logger.warning(f"Skipping {event.src_path}: no ISA header")
                return
            filename = os.path.basename(event.src_path)
            file_id = file_service.parse_and_store(raw, filename)
            logger.info(f"Auto-imported {filename} as file ID {file_id}")
        except Exception as e:
            logger.error(f"Error auto-importing {event.src_path}: {e}")


def start_watcher():
    """Start the file watcher if a watch directory is configured."""
    global _observer, _watch_thread

    watch_dir = get_setting("watch_directory")
    if not watch_dir or not os.path.isdir(watch_dir):
        logger.info("No valid watch directory configured, skipping file watcher")
        return

    stop_watcher()

    handler = ERAFileHandler()
    _observer = Observer()
    _observer.schedule(handler, watch_dir, recursive=False)
    _observer.daemon = True
    _observer.start()
    logger.info(f"File watcher started on: {watch_dir}")


def stop_watcher():
    """Stop the file watcher if running."""
    global _observer
    if _observer:
        _observer.stop()
        _observer.join(timeout=5)
        _observer = None
        logger.info("File watcher stopped")


def is_running() -> bool:
    """Check if the watcher is currently running."""
    return _observer is not None and _observer.is_alive()
