#!/usr/bin/env python3
"""
WebSocket test client for Retriever.

This script connects to the WebSocket endpoint and displays live updates
as documents are modified.

Usage:
    python scripts/test_websocket.py

Events received:
    - connected: Initial state on connection
    - document_updated: A file was modified/created/deleted
    - reindex_complete: Re-indexing finished for a file
    - pong: Response to ping
    - status: Response to status request
"""

import asyncio
import json
import sys
from datetime import datetime

try:
    import websockets
except ImportError:
    print("Please install websockets: pip install websockets")
    sys.exit(1)


async def listen_for_updates():
    """Connect to WebSocket and listen for updates."""
    uri = "ws://localhost:8000/ws"

    print(f"Connecting to {uri}...")
    print("-" * 60)

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for events...")
            print("(Modify a document in the documents/ folder to see live updates)")
            print("-" * 60)

            while True:
                try:
                    message = await websocket.recv()
                    event = json.loads(message)

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    event_type = event.get("event", "unknown")

                    if event_type == "connected":
                        status = event.get("status", {})
                        print(f"[{timestamp}] CONNECTED")
                        print(f"    Documents indexed: {status.get('documents_indexed', 0)}")
                        print(f"    Watcher active: {status.get('watcher_active', False)}")
                        print(f"    Last sync: {status.get('last_sync', 'Never')}")
                        docs = status.get("documents", [])
                        if docs:
                            print(f"    Files: {', '.join(docs)}")

                    elif event_type == "document_updated":
                        print(f"[{timestamp}] DOCUMENT UPDATED")
                        print(f"    File: {event.get('file', 'unknown')}")
                        print(f"    Type: {event.get('type', 'unknown')}")

                    elif event_type == "reindex_complete":
                        print(f"[{timestamp}] REINDEX COMPLETE")
                        print(f"    File: {event.get('file', 'unknown')}")
                        print(f"    Time: {event.get('time_ms', 0):.0f}ms")

                    elif event_type == "pong":
                        print(f"[{timestamp}] PONG received")

                    elif event_type == "status":
                        print(f"[{timestamp}] STATUS UPDATE")
                        print(f"    Documents: {event.get('documents_indexed', 0)}")
                        print(f"    Watcher: {event.get('watcher_active', False)}")

                    else:
                        print(f"[{timestamp}] {event_type.upper()}")
                        print(f"    {json.dumps(event, indent=4)}")

                    print("-" * 60)

                except websockets.exceptions.ConnectionClosed:
                    print("Connection closed by server")
                    break

    except ConnectionRefusedError:
        print("ERROR: Could not connect to server. Is it running?")
        print("Start the server with: cd backend && uvicorn main:app --reload")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


async def main():
    """Main entry point."""
    print("=" * 60)
    print("  Retriever WebSocket Test Client")
    print("=" * 60)
    print()

    await listen_for_updates()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDisconnected.")
