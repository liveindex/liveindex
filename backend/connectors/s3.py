"""
AWS S3 Connector

Connect to AWS S3 buckets for document ingestion and sync.

Required credentials:
    - aws_access_key_id: AWS Access Key ID
    - aws_secret_access_key: AWS Secret Access Key
    - region: AWS Region (e.g., "us-east-1")

Settings:
    - bucket: S3 bucket name
    - prefix: (optional) Key prefix to filter objects
    - use_iam_role: (optional) Use IAM role instead of credentials
"""

from typing import Any, Callable, Dict, List, Optional

from .base import (
    BaseConnector,
    ConnectorConfig,
    Document,
)


class S3Connector(BaseConnector):
    """
    Connector for AWS S3 documents.

    Syncs documents from S3 buckets with support for various file formats.
    Uses S3 Event Notifications for real-time change detection.
    """

    CONNECTOR_TYPE = "s3"
    CONNECTOR_NAME = "AWS S3"
    CONNECTOR_DESCRIPTION = "Connect to AWS S3 buckets"

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.bucket = config.settings.get("bucket")
        self.prefix = config.settings.get("prefix", "")
        self.use_iam_role = config.settings.get("use_iam_role", False)

    def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with AWS using credentials or IAM role."""
        # TODO: Implement AWS authentication
        # 1. Create boto3 client with credentials or IAM role
        # 2. Verify access with s3:ListBucket permission
        # 3. Store authenticated client
        raise NotImplementedError(
            "S3 connector not yet implemented. "
            "Contributions welcome! See README.md for implementation guide."
        )

    def list_documents(self, path: Optional[str] = None) -> List[Document]:
        """List documents from S3 bucket."""
        # TODO: Implement using boto3 list_objects_v2
        # - Handle pagination with ContinuationToken
        # - Filter by prefix
        # - Skip directories (keys ending with /)
        raise NotImplementedError("S3 connector not yet implemented.")

    def get_document(self, doc_id: str) -> Optional[Document]:
        """Get a document by S3 key."""
        # TODO: Implement using boto3 get_object
        # - Fetch object metadata and content
        # - Handle different content types
        # - Support text extraction from common formats
        raise NotImplementedError("S3 connector not yet implemented.")

    def watch_changes(self, callback: Callable[[str, str, Optional[Document]], None]) -> None:
        """Watch for changes using S3 Event Notifications."""
        # TODO: Implement using S3 Event Notifications + SQS/SNS
        # - Configure bucket notifications if not already set
        # - Poll SQS queue for change events
        # - Process events and invoke callback
        raise NotImplementedError("S3 connector not yet implemented.")

    def stop_watching(self) -> None:
        """Stop watching for changes."""
        # TODO: Stop polling SQS queue
        raise NotImplementedError("S3 connector not yet implemented.")

    def get_permissions(self, doc_id: str) -> List[str]:
        """Get permissions from S3 object ACL or bucket policy."""
        # TODO: Implement using boto3 get_object_acl
        # - Parse ACL grants
        # - Map AWS principals to LiveIndex roles
        # - Consider bucket policy for default permissions
        raise NotImplementedError("S3 connector not yet implemented.")
