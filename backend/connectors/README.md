# LiveIndex Connectors

Connectors allow LiveIndex to ingest documents from various data sources. Each connector implements a standard interface for authentication, document listing, content retrieval, and real-time change detection.

## Available Connectors

| Connector | Status | Description |
|-----------|--------|-------------|
| `local_files` | **Implemented** | Local filesystem with watchdog monitoring |
| `google_drive` | Stub | Google Drive documents and folders |
| `s3` | Stub | AWS S3 buckets |
| `notion` | Stub | Notion pages and databases |
| `slack` | Stub | Slack messages and files |
| `confluence` | Stub | Confluence pages and spaces |

## Implementing a Connector

### 1. Create Your Connector File

Create a new file in `backend/connectors/` (e.g., `my_connector.py`):

```python
from typing import Any, Callable, Dict, List, Optional

from .base import (
    BaseConnector,
    ConnectorConfig,
    Document,
)


class MyConnector(BaseConnector):
    """Your connector description."""

    CONNECTOR_TYPE = "my_connector"
    CONNECTOR_NAME = "My Connector"
    CONNECTOR_DESCRIPTION = "Connect to My Service"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        # Initialize connector-specific settings from config.settings
        self.my_setting = config.settings.get("my_setting", "default")
```

### 2. Implement Required Methods

Every connector must implement these methods from `BaseConnector`:

#### `authenticate(credentials) -> bool`

Authenticate with the data source. Return `True` on success.

```python
def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
    creds = credentials or self.config.credentials
    # Validate credentials and establish connection
    # Store authenticated client for later use
    self._client = create_client(creds)
    return True
```

#### `list_documents(path) -> List[Document]`

List all documents from the source. Handle pagination internally.

```python
def list_documents(self, path: Optional[str] = None) -> List[Document]:
    documents = []
    for item in self._client.list_items(path):
        doc = Document(
            id=item.id,
            name=item.name,
            path=item.path,
            content="",  # Content fetched separately
            content_type=item.mime_type,
            size=item.size,
            created_at=item.created,
            updated_at=item.modified,
            metadata={"source": self.CONNECTOR_TYPE},
        )
        documents.append(doc)
    return documents
```

#### `get_document(doc_id) -> Optional[Document]`

Retrieve a single document with full content.

```python
def get_document(self, doc_id: str) -> Optional[Document]:
    item = self._client.get_item(doc_id)
    if not item:
        return None

    content = self._client.download_content(doc_id)

    return Document(
        id=item.id,
        name=item.name,
        path=item.path,
        content=content,
        content_type=item.mime_type,
        size=len(content),
        updated_at=item.modified,
    )
```

#### `watch_changes(callback) -> None`

Start watching for changes. Call the callback when changes occur.

```python
def watch_changes(
    self,
    callback: Callable[[str, str, Optional[Document]], None]
) -> None:
    """
    Callback signature: callback(event_type, doc_id, document)
    - event_type: "created", "modified", or "deleted"
    - doc_id: The document identifier
    - document: The Document object (None for deletions)
    """
    def on_change(event):
        if event.type == "created":
            doc = self.get_document(event.item_id)
            callback("created", event.item_id, doc)
        elif event.type == "modified":
            doc = self.get_document(event.item_id)
            callback("modified", event.item_id, doc)
        elif event.type == "deleted":
            callback("deleted", event.item_id, None)

    self._watcher = self._client.watch(on_change)
```

#### `stop_watching() -> None`

Stop the change watcher.

```python
def stop_watching(self) -> None:
    if self._watcher:
        self._watcher.stop()
        self._watcher = None
```

#### `get_permissions(doc_id) -> List[str]`

Get permission identifiers for a document.

```python
def get_permissions(self, doc_id: str) -> List[str]:
    # Return list of user/group identifiers with access
    permissions = self._client.get_permissions(doc_id)
    return [p.principal_id for p in permissions]
```

### 3. Register Your Connector

Add your connector to `backend/connectors/__init__.py`:

```python
from .my_connector import MyConnector

CONNECTORS = {
    "local_files": LocalFilesConnector,
    "my_connector": MyConnector,  # Add this line
    # ...
}
```

## The Document Model

```python
@dataclass
class Document:
    id: str                              # Unique identifier
    name: str                            # Display name
    path: str                            # Full path or URL
    content: str                         # Document text content
    content_type: str = "text/plain"     # MIME type
    size: int = 0                        # Size in bytes
    created_at: Optional[datetime]       # Creation timestamp
    updated_at: Optional[datetime]       # Last modified timestamp
    metadata: Dict[str, Any]             # Additional metadata
    permissions: List[str]               # Access control list
```

## The ConnectorConfig Model

```python
@dataclass
class ConnectorConfig:
    connector_type: str                  # e.g., "google_drive"
    credentials: Dict[str, Any]          # Auth credentials
    settings: Dict[str, Any]             # Connector-specific settings
    name: Optional[str]                  # Display name
    enabled: bool = True                 # Is connector active
```

## Example: LocalFilesConnector

See `local_files.py` for a complete reference implementation:

- Uses `watchdog` for filesystem monitoring
- Supports multiple file extensions (`.txt`, `.md`, `.json`, etc.)
- Handles atomic writes (temp file → rename pattern)
- Extracts permissions from file metadata

Key patterns to follow:
1. Store authenticated state in instance variables
2. Handle pagination/batching in `list_documents`
3. Clean up resources in `stop_watching`
4. Return empty list (not None) when no documents found

## Testing Your Connector

```python
from connectors import get_connector

# Create connector instance
config = ConnectorConfig(
    connector_type="my_connector",
    credentials={"api_key": "..."},
    settings={"my_setting": "value"},
)

connector = get_connector(config)

# Test authentication
assert connector.authenticate()

# Test document listing
docs = connector.list_documents()
print(f"Found {len(docs)} documents")

# Test document retrieval
if docs:
    doc = connector.get_document(docs[0].id)
    print(f"Content: {doc.content[:100]}...")

# Test change watching
def on_change(event_type, doc_id, doc):
    print(f"{event_type}: {doc_id}")

connector.watch_changes(on_change)
# ... make changes to test ...
connector.stop_watching()
```

## Contributions Welcome!

We'd love help implementing the stub connectors! To contribute:

1. Pick a stub connector (`google_drive`, `s3`, `notion`, `slack`, `confluence`)
2. Implement all required methods
3. Add tests
4. Submit a PR

### Implementation Tips

- **Google Drive**: Use `google-api-python-client`, OAuth 2.0 flow
- **S3**: Use `boto3`, support both credentials and IAM roles
- **Notion**: Use `notion-client`, handle block-based content
- **Slack**: Use `slack-sdk`, Socket Mode for real-time events
- **Confluence**: Use REST API with Basic auth (email:api_token)

### Questions?

Open an issue or reach out to the maintainers. Happy building!
