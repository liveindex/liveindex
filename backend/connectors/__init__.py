"""
LiveIndex Connectors

A plugin architecture for connecting to various document sources.
Each connector implements the BaseConnector interface to provide
unified access to documents from different platforms.
"""

from .base import BaseConnector, Document, ConnectorConfig
from .local_files import LocalFilesConnector

__all__ = [
    "BaseConnector",
    "Document",
    "ConnectorConfig",
    "LocalFilesConnector",
]
