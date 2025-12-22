"""
Local Files Connector

Connects to local filesystem for document ingestion and real-time monitoring.
This is the reference implementation of the BaseConnector interface.
"""

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .base import (
    BaseConnector,
    ConnectorConfig,
    Document,
    AuthenticationError,
    DocumentNotFoundError,
)


# Supported file extensions
SUPPORTED_EXTENSIONS = {".md", ".txt", ".markdown", ".rst", ".html"}

# Debounce delay for file changes (seconds)
DEBOUNCE_DELAY = 0.5


class LocalFilesEventHandler(FileSystemEventHandler):
    """Handles filesystem events and debounces rapid changes."""

    def __init__(self, callback: Callable[[str, str], None], base_dir: str):
        super().__init__()
        self.callback = callback
        self.base_dir = base_dir
        self._pending: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._debounce_thread: Optional[threading.Thread] = None

    def _is_supported(self, path: str) -> bool:
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def _schedule(self, path: str, event_type: str):
        with self._lock:
            self._pending[path] = {"type": event_type, "time": time.time()}

        if self._debounce_thread is None or not self._debounce_thread.is_alive():
            self._debounce_thread = threading.Thread(target=self._process_pending)
            self._debounce_thread.daemon = True
            self._debounce_thread.start()

    def _process_pending(self):
        time.sleep(DEBOUNCE_DELAY)
        with self._lock:
            changes = self._pending.copy()
            self._pending.clear()

        for path, info in changes.items():
            event_type = info["type"]
            # Handle atomic writes (temp file -> rename pattern)
            if event_type == "deleted" and os.path.exists(path):
                event_type = "modified"
            self.callback(path, event_type)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory and self._is_supported(event.src_path):
            self._schedule(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory and self._is_supported(event.src_path):
            self._schedule(event.src_path, "modified")

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory and self._is_supported(event.src_path):
            self._schedule(event.src_path, "deleted")

    def on_moved(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self._is_supported(event.src_path):
            self._schedule(event.src_path, "deleted")
        if self._is_supported(event.dest_path):
            self._schedule(event.dest_path, "created")


class LocalFilesConnector(BaseConnector):
    """
    Connector for local filesystem documents.

    This connector monitors a local directory for document changes and
    provides real-time sync capabilities using the watchdog library.

    Example:
        config = ConnectorConfig(
            name="my-docs",
            connector_type="local_files",
            settings={"directory": "/path/to/documents"}
        )
        connector = LocalFilesConnector(config)
        connector.authenticate()
        docs = connector.list_documents()
    """

    CONNECTOR_TYPE = "local_files"
    CONNECTOR_NAME = "Local Files"
    CONNECTOR_DESCRIPTION = "Connect to local filesystem documents"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.directory = config.settings.get("directory", ".")
        self._observer: Optional[Observer] = None
        self._callback: Optional[Callable] = None

    def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """
        Verify the directory exists and is readable.

        For local files, authentication just means checking directory access.
        """
        try:
            directory = Path(self.directory)
            if not directory.exists():
                raise AuthenticationError(f"Directory not found: {self.directory}")
            if not directory.is_dir():
                raise AuthenticationError(f"Path is not a directory: {self.directory}")
            if not os.access(self.directory, os.R_OK):
                raise AuthenticationError(f"Directory not readable: {self.directory}")

            self._authenticated = True
            return True
        except OSError as e:
            raise AuthenticationError(f"Cannot access directory: {e}")

    def list_documents(self, path: Optional[str] = None) -> List[Document]:
        """List all supported documents in the directory."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        search_path = Path(path) if path else Path(self.directory)
        documents = []

        for file_path in search_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                doc = self._path_to_document(file_path)
                if doc:
                    documents.append(doc)

        return documents

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by its path (relative to base directory)."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        file_path = Path(self.directory) / doc_id
        if not file_path.exists():
            return None
        return self._path_to_document(file_path)

    def watch_changes(self, callback: Callable[[str, str, Optional[Document]], None]) -> None:
        """Start watching the directory for changes."""
        if not self._authenticated:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        if self._watching:
            return

        def handle_change(path: str, event_type: str):
            doc_id = os.path.relpath(path, self.directory)
            document = None if event_type == "deleted" else self._path_to_document(Path(path))
            callback(event_type, doc_id, document)

        handler = LocalFilesEventHandler(handle_change, self.directory)
        self._observer = Observer()
        self._observer.schedule(handler, self.directory, recursive=True)
        self._observer.start()
        self._watching = True

    def stop_watching(self) -> None:
        """Stop watching for changes."""
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        self._watching = False

    def get_permissions(self, doc_id: str) -> List[str]:
        """
        Get permissions for a document.

        For local files, permissions are based on the folder structure:
        - policies/security-* -> ["admin"]
        - policies/employee-* -> ["manager", "admin"]
        - everything else -> [] (public)
        """
        doc_id_lower = doc_id.lower()

        if "security" in doc_id_lower:
            return ["admin"]
        elif "employee" in doc_id_lower or "handbook" in doc_id_lower:
            return ["manager", "admin"]
        else:
            return []  # Public

    def _path_to_document(self, file_path: Path) -> Optional[Document]:
        """Convert a file path to a Document object."""
        try:
            stat = file_path.stat()
            content = file_path.read_text(encoding="utf-8")
            doc_id = os.path.relpath(file_path, self.directory)

            return Document(
                id=doc_id,
                name=file_path.name,
                path=str(file_path),
                content=content,
                content_type=self._get_content_type(file_path),
                size=stat.st_size,
                created_at=datetime.fromtimestamp(stat.st_ctime),
                updated_at=datetime.fromtimestamp(stat.st_mtime),
                metadata={
                    "extension": file_path.suffix,
                    "directory": str(file_path.parent),
                },
                permissions=self.get_permissions(doc_id),
            )
        except Exception:
            return None

    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME type based on file extension."""
        ext = file_path.suffix.lower()
        return {
            ".md": "text/markdown",
            ".markdown": "text/markdown",
            ".txt": "text/plain",
            ".rst": "text/x-rst",
            ".html": "text/html",
        }.get(ext, "text/plain")

    def health_check(self) -> Dict[str, Any]:
        """Check connector health."""
        base = super().health_check()
        base["details"] = {
            "directory": self.directory,
            "exists": os.path.exists(self.directory),
            "readable": os.access(self.directory, os.R_OK) if os.path.exists(self.directory) else False,
        }
        return base
