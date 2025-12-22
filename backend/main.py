import os
import asyncio
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from dotenv import load_dotenv

from ingestion import ingest_directory
from query import search_documents, get_unique_documents
from watcher import DocumentWatcher

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
DOCUMENTS_PATH = os.getenv("DOCUMENTS_PATH", "./documents")

# Global state
qdrant_client: Optional[QdrantClient] = None
document_watcher: Optional[DocumentWatcher] = None
connected_websockets: List[WebSocket] = []


# Store reference to main event loop
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def on_file_change(file_path: str, event_type: str):
    """Callback when a file changes - broadcast to WebSocket clients."""
    event = {
        "event": "document_updated",
        "file": file_path,
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    # Schedule the broadcast in the event loop
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(event), _main_loop)


def on_reindex_complete(file_path: str, time_ms: float):
    """Callback when re-indexing completes - broadcast to WebSocket clients."""
    event = {
        "event": "reindex_complete",
        "file": file_path,
        "time_ms": round(time_ms, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
    # Schedule the broadcast in the event loop
    if _main_loop and _main_loop.is_running():
        asyncio.run_coroutine_threadsafe(broadcast_event(event), _main_loop)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    global qdrant_client, document_watcher, _main_loop

    # Store reference to main event loop for cross-thread callbacks
    _main_loop = asyncio.get_running_loop()

    # Startup
    logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    logger.info("Connected to Qdrant")

    # Start file watcher if documents path exists
    docs_path = os.path.abspath(DOCUMENTS_PATH)
    if os.path.exists(docs_path):
        document_watcher = DocumentWatcher(
            directory=docs_path,
            on_file_change=on_file_change,
            on_reindex_complete=on_reindex_complete,
        )
        document_watcher.start(loop=_main_loop)
        logger.info(f"File watcher started for: {docs_path}")
    else:
        logger.warning(f"Documents path not found: {docs_path}")

    yield

    # Shutdown
    if document_watcher:
        document_watcher.stop()
        logger.info("File watcher stopped")

    if qdrant_client:
        qdrant_client.close()
        logger.info("Disconnected from Qdrant")


app = FastAPI(
    title="LiveIndex",
    description="Real-time knowledge infrastructure for AI",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class IngestRequest(BaseModel):
    directory: str


class IngestResponse(BaseModel):
    status: str
    documents_ingested: int
    time_seconds: float


class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class SourceResult(BaseModel):
    file: str
    chunk: str
    score: float
    updated_at: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceResult]
    latency_ms: float


class StatusResponse(BaseModel):
    documents_indexed: int
    last_sync: Optional[str]
    watcher_active: bool
    qdrant_connected: bool


# Endpoints
@app.get("/health")
async def health():
    """Health check endpoint."""
    qdrant_ok = False
    try:
        if qdrant_client:
            qdrant_client.get_collections()
            qdrant_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if qdrant_ok else "degraded",
        "qdrant": "connected" if qdrant_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current system status."""
    qdrant_ok = False
    doc_count = 0

    try:
        if qdrant_client:
            qdrant_client.get_collections()
            qdrant_ok = True
            # Try to get document count from our collection
            try:
                collection_info = qdrant_client.get_collection("documents")
                doc_count = collection_info.points_count
            except UnexpectedResponse:
                pass  # Collection doesn't exist yet
    except Exception:
        pass

    # Get watcher status
    watcher_active = document_watcher.running if document_watcher else False
    last_sync = None
    if document_watcher and document_watcher.last_sync:
        last_sync = document_watcher.last_sync.isoformat()

    return StatusResponse(
        documents_indexed=doc_count,
        last_sync=last_sync,
        watcher_active=watcher_active,
        qdrant_connected=qdrant_ok,
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(request: IngestRequest):
    """Ingest documents from a directory."""
    result = await ingest_directory(request.directory)
    return IngestResponse(
        status=result["status"],
        documents_ingested=result["documents_ingested"],
        time_seconds=result["time_seconds"],
    )


@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the document index."""
    result = await search_documents(request.query, request.top_k)

    # Convert source dicts to SourceResult models
    sources = [
        SourceResult(
            file=s["file"],
            chunk=s["chunk"],
            score=s["score"],
            updated_at=s["updated_at"],
        )
        for s in result["sources"]
    ]

    return QueryResponse(
        answer=result["answer"],
        sources=sources,
        latency_ms=result["latency_ms"],
    )


@app.get("/documents")
async def list_documents():
    """List all indexed documents."""
    documents = await get_unique_documents()
    return {"documents": documents, "count": len(documents)}


class WatcherRequest(BaseModel):
    directory: Optional[str] = None


@app.post("/watcher/start")
async def start_watcher(request: WatcherRequest = None):
    """Start the file watcher."""
    global document_watcher

    directory = DOCUMENTS_PATH
    if request and request.directory:
        directory = request.directory

    directory = os.path.abspath(directory)

    if not os.path.exists(directory):
        return {"status": "error", "message": f"Directory not found: {directory}"}

    if document_watcher and document_watcher.running:
        return {"status": "already_running", "directory": document_watcher.directory}

    document_watcher = DocumentWatcher(
        directory=directory,
        on_file_change=on_file_change,
        on_reindex_complete=on_reindex_complete,
    )
    document_watcher.start(loop=asyncio.get_event_loop())

    return {"status": "started", "directory": directory}


@app.post("/watcher/stop")
async def stop_watcher():
    """Stop the file watcher."""
    global document_watcher

    if not document_watcher or not document_watcher.running:
        return {"status": "not_running"}

    document_watcher.stop()
    return {"status": "stopped"}


@app.get("/watcher/status")
async def watcher_status():
    """Get file watcher status."""
    if not document_watcher:
        return {
            "running": False,
            "directory": None,
            "last_sync": None,
        }

    return {
        "running": document_watcher.running,
        "directory": document_watcher.directory if document_watcher.running else None,
        "last_sync": document_watcher.last_sync.isoformat() if document_watcher.last_sync else None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sync notifications."""
    await websocket.accept()
    connected_websockets.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(connected_websockets)}")

    # Send initial state on connect
    try:
        doc_count = 0
        try:
            if qdrant_client:
                collection_info = qdrant_client.get_collection("documents")
                doc_count = collection_info.points_count
        except Exception:
            pass

        documents = await get_unique_documents()

        initial_state = {
            "event": "connected",
            "status": {
                "documents_indexed": doc_count,
                "documents": documents,
                "watcher_active": document_watcher.running if document_watcher else False,
                "last_sync": document_watcher.last_sync.isoformat() if document_watcher and document_watcher.last_sync else None,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_json(initial_state)
    except Exception as e:
        logger.error(f"Failed to send initial state: {e}")

    try:
        while True:
            # Wait for messages (ping/pong or commands)
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")

            # Handle ping
            if data == "ping":
                await websocket.send_json({"event": "pong", "timestamp": datetime.utcnow().isoformat()})
            # Handle status request
            elif data == "status":
                doc_count = 0
                try:
                    if qdrant_client:
                        collection_info = qdrant_client.get_collection("documents")
                        doc_count = collection_info.points_count
                except Exception:
                    pass

                documents = await get_unique_documents()
                status = {
                    "event": "status",
                    "documents_indexed": doc_count,
                    "documents": documents,
                    "watcher_active": document_watcher.running if document_watcher else False,
                    "last_sync": document_watcher.last_sync.isoformat() if document_watcher and document_watcher.last_sync else None,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                await websocket.send_json(status)

    except WebSocketDisconnect:
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(connected_websockets)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)


async def broadcast_event(event: dict):
    """Broadcast an event to all connected WebSocket clients."""
    disconnected = []
    for ws in connected_websockets:
        try:
            await ws.send_json(event)
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            disconnected.append(ws)

    # Clean up disconnected clients
    for ws in disconnected:
        if ws in connected_websockets:
            connected_websockets.remove(ws)

    if disconnected:
        logger.info(f"Cleaned up {len(disconnected)} disconnected clients. Total: {len(connected_websockets)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
