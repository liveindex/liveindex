"""
File system watcher for real-time document updates.

This module monitors the documents directory for changes and triggers re-indexing.
"""

import os
import asyncio
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, Set

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

# Supported file extensions
SUPPORTED_EXTENSIONS = {".md", ".txt", ".markdown"}

# Debounce delay in seconds (to avoid multiple re-indexes for rapid changes)
DEBOUNCE_DELAY = 0.5


class DocumentEventHandler(FileSystemEventHandler):
    """Handles file system events for document changes."""

    def __init__(
        self,
        on_change: Callable[[str, str], None],
        base_dir: str,
    ):
        super().__init__()
        self.on_change = on_change
        self.base_dir = base_dir
        self._pending_changes: dict = {}
        self._lock = threading.Lock()
        self._debounce_thread: Optional[threading.Thread] = None

    def _is_supported_file(self, path: str) -> bool:
        """Check if the file has a supported extension."""
        return Path(path).suffix.lower() in SUPPORTED_EXTENSIONS

    def _schedule_change(self, path: str, event_type: str):
        """Schedule a change with debouncing."""
        with self._lock:
            self._pending_changes[path] = {
                "type": event_type,
                "time": time.time(),
            }

        # Start debounce thread if not running
        if self._debounce_thread is None or not self._debounce_thread.is_alive():
            self._debounce_thread = threading.Thread(target=self._process_pending)
            self._debounce_thread.daemon = True
            self._debounce_thread.start()

    def _process_pending(self):
        """Process pending changes after debounce delay."""
        time.sleep(DEBOUNCE_DELAY)

        with self._lock:
            changes = self._pending_changes.copy()
            self._pending_changes.clear()

        for path, info in changes.items():
            try:
                event_type = info["type"]

                # For delete events, check if file still exists (atomic write pattern)
                # Editors often: write temp -> delete original -> rename temp to original
                # This causes a brief "deleted" state even though file will exist
                if event_type == "deleted":
                    if os.path.exists(path):
                        logger.info(f"File exists after delete event (atomic write): {path}")
                        event_type = "modified"  # Treat as modification instead
                    else:
                        # Double-check after a short delay for slow filesystems
                        time.sleep(0.1)
                        if os.path.exists(path):
                            logger.info(f"File appeared after delete (atomic write): {path}")
                            event_type = "modified"

                self.on_change(path, event_type)
            except Exception as e:
                logger.error(f"Error processing change for {path}: {e}")

    def on_created(self, event: FileSystemEvent):
        """Handle file creation."""
        if event.is_directory:
            return
        if self._is_supported_file(event.src_path):
            logger.info(f"File created: {event.src_path}")
            self._schedule_change(event.src_path, "created")

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification."""
        if event.is_directory:
            return
        if self._is_supported_file(event.src_path):
            logger.info(f"File modified: {event.src_path}")
            self._schedule_change(event.src_path, "modified")

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion."""
        if event.is_directory:
            return
        if self._is_supported_file(event.src_path):
            logger.info(f"File deleted: {event.src_path}")
            self._schedule_change(event.src_path, "deleted")

    def on_moved(self, event: FileSystemEvent):
        """Handle file move/rename."""
        if event.is_directory:
            return

        # Handle source (old path)
        if self._is_supported_file(event.src_path):
            logger.info(f"File moved from: {event.src_path}")
            self._schedule_change(event.src_path, "deleted")

        # Handle destination (new path)
        if self._is_supported_file(event.dest_path):
            logger.info(f"File moved to: {event.dest_path}")
            self._schedule_change(event.dest_path, "created")


class DocumentWatcher:
    """Watches a directory for file changes and triggers re-indexing."""

    def __init__(
        self,
        directory: str,
        on_file_change: Optional[Callable[[str, str], None]] = None,
        on_reindex_complete: Optional[Callable[[str, float], None]] = None,
    ):
        self.directory = os.path.abspath(directory)
        self.on_file_change = on_file_change
        self.on_reindex_complete = on_reindex_complete
        self.running = False
        self._observer: Optional[Observer] = None
        self._last_sync: Optional[datetime] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _handle_change(self, path: str, event_type: str):
        """Handle a file change event."""
        relative_path = os.path.relpath(path, self.directory)

        # Notify about the change
        if self.on_file_change:
            self.on_file_change(relative_path, event_type)

        # Trigger re-indexing
        self._reindex_file(path, event_type)

    def _reindex_file(self, path: str, event_type: str):
        """Re-index a single file."""
        from ingestion import ingest_file, delete_file_chunks

        start_time = time.time()
        relative_path = os.path.relpath(path, self.directory)

        try:
            if not self._loop:
                logger.error("No event loop available for re-indexing")
                return

            if event_type == "deleted":
                # Remove chunks for deleted file
                future = asyncio.run_coroutine_threadsafe(
                    delete_file_chunks(path, self.directory),
                    self._loop
                )
                future.result(timeout=30)
                logger.info(f"Removed index for deleted file: {relative_path}")
            else:
                # Check if file exists (might have been deleted quickly)
                if not os.path.exists(path):
                    logger.warning(f"File no longer exists: {relative_path}")
                    return

                # Re-ingest the file
                future = asyncio.run_coroutine_threadsafe(
                    ingest_file(path, base_dir=self.directory),
                    self._loop
                )
                result = future.result(timeout=60)
                logger.info(f"Re-indexed {relative_path}: {result.get('chunks_created', 0)} chunks")

            elapsed = time.time() - start_time
            self._last_sync = datetime.utcnow()

            # Notify about reindex completion
            if self.on_reindex_complete:
                self.on_reindex_complete(relative_path, elapsed * 1000)

        except Exception as e:
            logger.error(f"Failed to re-index {relative_path}: {e}")

    def start(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Start watching the directory."""
        if self.running:
            logger.warning("Watcher is already running")
            return

        self._loop = loop or asyncio.get_event_loop()

        # Create event handler
        event_handler = DocumentEventHandler(
            on_change=self._handle_change,
            base_dir=self.directory,
        )

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(event_handler, self.directory, recursive=True)
        self._observer.start()

        self.running = True
        logger.info(f"Started watching: {self.directory}")

    def stop(self):
        """Stop watching the directory."""
        if not self.running:
            return

        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None

        self.running = False
        logger.info("Stopped file watcher")

    @property
    def last_sync(self) -> Optional[datetime]:
        """Get the timestamp of the last sync operation."""
        return self._last_sync
