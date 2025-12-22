"""
Base Connector Interface

All connectors must implement this abstract base class to integrate
with LiveIndex's document ingestion and real-time sync pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Document:
    """Represents a document from any source."""

    id: str                          # Unique identifier within the connector
    name: str                        # Display name
    path: str                        # Full path or URL
    content: str                     # Document content (text)
    content_type: str = "text/plain" # MIME type
    size: int = 0                    # Size in bytes
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)  # List of role/user IDs with access


@dataclass
class ConnectorConfig:
    """Configuration for a connector instance."""

    name: str                        # Connector instance name
    connector_type: str              # Type identifier (e.g., "local_files", "google_drive")
    credentials: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


class BaseConnector(ABC):
    """
    Abstract base class for all document source connectors.

    Implement this interface to add support for a new document source.
    See LocalFilesConnector for a reference implementation.
    """

    # Connector metadata
    CONNECTOR_TYPE: str = "base"
    CONNECTOR_NAME: str = "Base Connector"
    CONNECTOR_DESCRIPTION: str = "Abstract base connector"

    def __init__(self, config: ConnectorConfig):
        """
        Initialize the connector with configuration.

        Args:
            config: Connector configuration including credentials and settings
        """
        self.config = config
        self._authenticated = False
        self._watching = False

    @property
    def is_authenticated(self) -> bool:
        """Check if connector is authenticated."""
        return self._authenticated

    @property
    def is_watching(self) -> bool:
        """Check if connector is watching for changes."""
        return self._watching

    @abstractmethod
    def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authenticate with the document source.

        Args:
            credentials: Optional credentials dict. If None, use config credentials.

        Returns:
            True if authentication successful, False otherwise.

        Raises:
            AuthenticationError: If authentication fails with an error.
        """
        pass

    @abstractmethod
    def list_documents(self, path: Optional[str] = None) -> List[Document]:
        """
        List all documents from the source.

        Args:
            path: Optional path/folder to list documents from.
                  If None, list all accessible documents.

        Returns:
            List of Document objects.

        Raises:
            ConnectionError: If unable to connect to source.
            PermissionError: If access is denied.
        """
        pass

    @abstractmethod
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Retrieve a single document by ID.

        Args:
            doc_id: Unique document identifier.

        Returns:
            Document object if found, None otherwise.

        Raises:
            ConnectionError: If unable to connect to source.
            PermissionError: If access is denied.
        """
        pass

    @abstractmethod
    def watch_changes(self, callback: Callable[[str, str, Optional[Document]], None]) -> None:
        """
        Start watching for document changes.

        The callback will be invoked when documents are created, modified, or deleted.

        Args:
            callback: Function called on changes with signature:
                     callback(event_type: str, doc_id: str, document: Optional[Document])

                     event_type: "created", "modified", or "deleted"
                     doc_id: Document identifier
                     document: Document object (None for deletions)

        Note:
            Call stop_watching() to stop the watch.
        """
        pass

    @abstractmethod
    def stop_watching(self) -> None:
        """Stop watching for document changes."""
        pass

    @abstractmethod
    def get_permissions(self, doc_id: str) -> List[str]:
        """
        Get permission list for a document.

        Args:
            doc_id: Document identifier.

        Returns:
            List of role/user identifiers that have access to this document.
            Empty list means public access.

        Example:
            ["admin", "manager"]  # Only admin and manager roles can access
            ["user:123", "group:engineering"]  # Specific user and group
            []  # Public, everyone can access
        """
        pass

    def health_check(self) -> Dict[str, Any]:
        """
        Check connector health status.

        Returns:
            Dict with health information:
            {
                "healthy": bool,
                "authenticated": bool,
                "watching": bool,
                "message": str,
                "details": dict
            }
        """
        return {
            "healthy": self._authenticated,
            "authenticated": self._authenticated,
            "watching": self._watching,
            "message": "OK" if self._authenticated else "Not authenticated",
            "details": {}
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(type={self.CONNECTOR_TYPE}, authenticated={self._authenticated})>"


class ConnectorError(Exception):
    """Base exception for connector errors."""
    pass


class AuthenticationError(ConnectorError):
    """Raised when authentication fails."""
    pass


class DocumentNotFoundError(ConnectorError):
    """Raised when a document is not found."""
    pass
