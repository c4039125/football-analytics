"""
S3 handler for long-term data storage and archival.
"""

import json
import gzip
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import io

from ..models.event_models import BaseEvent
from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.aws_helpers import get_s3_client
from ..utils.metrics import get_metrics_collector

logger = get_logger(__name__)


class S3Handler:
    """
    S3 handler for data storage and retrieval.
    """

    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize S3 handler.

        Args:
            bucket_name: S3 bucket name (defaults to settings)
        """
        self.settings = get_settings()
        self.bucket_name = bucket_name or self.settings.s3_bucket_name
        self.s3_client = get_s3_client()
        self.metrics = get_metrics_collector()

        logger.info(f"Initialized S3 handler for bucket: {self.bucket_name}")

    def put_object(
        self,
        key: str,
        data: bytes,
        metadata: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Put an object to S3.

        Args:
            key: S3 object key
            data: Object data
            metadata: Optional metadata

        Returns:
            bool: True if successful
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=data,
                Metadata=metadata or {},
                ServerSideEncryption='aws:kms'
            )
            self.metrics.cost.s3_put_requests += 1
            logger.debug(f"Put object to S3: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to put object to S3", key=key, error=str(e))
            return False

    def get_object(self, key: str) -> Optional[bytes]:
        """
        Get an object from S3.

        Args:
            key: S3 object key

        Returns:
            bytes: Object data, or None if not found
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            self.metrics.cost.s3_get_requests += 1
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Failed to get object from S3", key=key, error=str(e))
            return None

    def list_objects(self, prefix: str, max_keys: int = 1000) -> List[str]:
        """
        List objects in S3 with a given prefix.

        Args:
            prefix: S3 key prefix
            max_keys: Maximum number of keys to return

        Returns:
            list: List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except Exception as e:
            logger.error(f"Failed to list objects in S3", prefix=prefix, error=str(e))
            return []


class DataArchiver:
    """
    High-level data archiver for long-term storage.
    """

    def __init__(self):
        """Initialize data archiver."""
        self.s3_handler = S3Handler()
        self.settings = get_settings()
        self.metrics = get_metrics_collector()

    def archive_match_data(
        self,
        match_id: str,
        events: List[BaseEvent],
        compress: bool = True
    ) -> bool:
        """
        Archive match data to S3.

        Args:
            match_id: Match identifier
            events: List of events to archive
            compress: Whether to compress data

        Returns:
            bool: True if successful
        """
        try:
            # Prepare data
            data = {
                'match_id': match_id,
                'archived_at': datetime.utcnow().isoformat(),
                'event_count': len(events),
                'events': [e.model_dump(mode='json') for e in events]
            }

            json_data = json.dumps(data).encode('utf-8')

            # Compress if requested
            if compress:
                buffer = io.BytesIO()
                with gzip.open(buffer, 'wb') as gz:
                    gz.write(json_data)
                data_to_store = buffer.getvalue()
                extension = '.json.gz'
            else:
                data_to_store = json_data
                extension = '.json'

            # Generate S3 key with date partitioning
            date = datetime.utcnow()
            key = f"{self.settings.s3_prefix}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{match_id}{extension}"

            # Store to S3
            success = self.s3_handler.put_object(
                key=key,
                data=data_to_store,
                metadata={
                    'match_id': match_id,
                    'event_count': str(len(events)),
                    'compressed': str(compress)
                }
            )

            if success:
                logger.info(
                    f"Archived match data to S3",
                    match_id=match_id,
                    event_count=len(events),
                    compressed=compress,
                    key=key
                )

            return success

        except Exception as e:
            logger.error(f"Failed to archive match data", match_id=match_id, error=str(e))
            return False

    def retrieve_match_data(self, match_id: str, date: datetime) -> Optional[Dict[str, Any]]:
        """
        Retrieve archived match data.

        Args:
            match_id: Match identifier
            date: Match date

        Returns:
            dict: Match data, or None if not found
        """
        try:
            # Try compressed first
            key = f"{self.settings.s3_prefix}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{match_id}.json.gz"
            data = self.s3_handler.get_object(key)

            if data:
                # Decompress
                with gzip.open(io.BytesIO(data), 'rb') as gz:
                    json_data = gz.read()
                return json.loads(json_data)

            # Try uncompressed
            key = f"{self.settings.s3_prefix}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{match_id}.json"
            data = self.s3_handler.get_object(key)

            if data:
                return json.loads(data)

            return None

        except Exception as e:
            logger.error(f"Failed to retrieve match data", match_id=match_id, error=str(e))
            return None
