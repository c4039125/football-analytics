"""
Kinesis producer for ingesting football events.
"""

import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from ..models.event_models import (
    BaseEvent,
    MatchEvent,
    PlayerTrackingEvent,
    PhysiologicalEvent,
    EventBatch,
)
from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.aws_helpers import get_kinesis_client, put_kinesis_records
from ..utils.metrics import get_metrics_collector

logger = get_logger(__name__)


class KinesisProducer:
    """
    Kinesis producer for event ingestion.
    Handles batching, partitioning, and retry logic.
    """

    def __init__(self, stream_name: Optional[str] = None):
        """
        Initialize Kinesis producer.

        Args:
            stream_name: Kinesis stream name (defaults to settings)
        """
        self.settings = get_settings()
        self.stream_name = stream_name or self.settings.kinesis_stream_name
        self.client = get_kinesis_client()
        self.metrics = get_metrics_collector()

        logger.info(
            "Initialized Kinesis producer",
            stream=self.stream_name,
            region=self.settings.aws_region
        )

    def _generate_partition_key(self, event: BaseEvent) -> str:
        """
        Generate partition key for event.
        Uses match_id to ensure all events for a match go to the same shard.

        Args:
            event: Event to partition

        Returns:
            str: Partition key
        """
        # Use match_id as partition key to ensure ordering per match
        return event.match_id

    def _serialize_event(self, event: BaseEvent) -> bytes:
        """
        Serialize event to JSON bytes.

        Args:
            event: Event to serialize

        Returns:
            bytes: Serialized event
        """
        # Convert Pydantic model to dict, then to JSON
        event_dict = event.model_dump(mode='json')

        # Add metadata
        event_dict['_ingestion_timestamp'] = datetime.utcnow().isoformat()

        return json.dumps(event_dict).encode('utf-8')

    def put_event(self, event: BaseEvent) -> bool:
        """
        Put a single event to Kinesis.

        Args:
            event: Event to ingest

        Returns:
            bool: True if successful
        """
        self.metrics.start_timer('ingestion')

        try:
            data = self._serialize_event(event)
            partition_key = self._generate_partition_key(event)

            response = self.client.put_record(
                StreamName=self.stream_name,
                Data=data,
                PartitionKey=partition_key
            )

            latency_ms = self.metrics.stop_timer('ingestion')
            self.metrics.record_latency('ingestion', latency_ms)
            self.metrics.cost.kinesis_put_records += 1

            logger.debug(
                "Put event to Kinesis",
                event_id=event.event_id,
                event_type=event.event_type,
                shard_id=response.get('ShardId'),
                sequence_number=response.get('SequenceNumber'),
                latency_ms=latency_ms
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to put event to Kinesis",
                event_id=event.event_id,
                error=str(e),
                exc_info=True
            )
            return False

    def put_events(self, events: List[BaseEvent]) -> Dict[str, Any]:
        """
        Put multiple events to Kinesis in a batch.

        Args:
            events: List of events to ingest

        Returns:
            dict: Result with success/failure counts
        """
        if not events:
            return {"success_count": 0, "failure_count": 0}

        self.metrics.start_timer('ingestion_batch')

        try:
            # Prepare records for batch put
            records = []
            for event in events:
                records.append({
                    'Data': self._serialize_event(event),
                    'PartitionKey': self._generate_partition_key(event)
                })

            # Put records in batches of 500 (Kinesis limit)
            batch_size = 500
            total_success = 0
            total_failed = 0
            failed_events = []

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]

                response = put_kinesis_records(self.stream_name, batch)

                failed_count = response.get('FailedRecordCount', 0)
                success_count = len(batch) - failed_count

                total_success += success_count
                total_failed += failed_count

                # Track failed records
                if failed_count > 0:
                    for idx, record in enumerate(response['Records']):
                        if 'ErrorCode' in record:
                            failed_events.append({
                                'event': events[i + idx].event_id,
                                'error': record.get('ErrorMessage', 'Unknown error')
                            })

                self.metrics.cost.kinesis_put_records += len(batch)

            latency_ms = self.metrics.stop_timer('ingestion_batch')
            self.metrics.record_latency('ingestion', latency_ms)

            logger.info(
                "Put batch to Kinesis",
                total_events=len(events),
                success_count=total_success,
                failed_count=total_failed,
                latency_ms=latency_ms
            )

            return {
                "success_count": total_success,
                "failure_count": total_failed,
                "failed_events": failed_events,
                "latency_ms": latency_ms
            }

        except Exception as e:
            logger.error(
                "Failed to put batch to Kinesis",
                event_count=len(events),
                error=str(e),
                exc_info=True
            )
            return {
                "success_count": 0,
                "failure_count": len(events),
                "error": str(e)
            }


class EventIngestionService:
    """
    High-level event ingestion service.
    Provides a simplified interface for ingesting different event types.
    """

    def __init__(self, stream_name: Optional[str] = None):
        """
        Initialize event ingestion service.

        Args:
            stream_name: Kinesis stream name
        """
        self.producer = KinesisProducer(stream_name)
        self.metrics = get_metrics_collector()
        self.settings = get_settings()

    def ingest_match_event(self, event: MatchEvent) -> bool:
        """
        Ingest a match event.

        Args:
            event: Match event

        Returns:
            bool: True if successful
        """
        return self.producer.put_event(event)

    def ingest_tracking_event(self, event: PlayerTrackingEvent) -> bool:
        """
        Ingest a player tracking event.

        Args:
            event: Tracking event

        Returns:
            bool: True if successful
        """
        return self.producer.put_event(event)

    def ingest_physiological_event(self, event: PhysiologicalEvent) -> bool:
        """
        Ingest a physiological event.

        Args:
            event: Physiological event

        Returns:
            bool: True if successful
        """
        return self.producer.put_event(event)

    def ingest_batch(self, batch: EventBatch) -> Dict[str, Any]:
        """
        Ingest an event batch.

        Args:
            batch: Event batch

        Returns:
            dict: Ingestion results
        """
        # Flatten all events from batch
        all_events = []
        all_events.extend(batch.match_events)
        all_events.extend(batch.tracking_events)
        all_events.extend(batch.physiological_events)
        all_events.extend(batch.ball_tracking_events)

        logger.info(
            "Ingesting event batch",
            batch_id=batch.batch_id,
            match_id=batch.match_id,
            total_events=batch.total_events
        )

        result = self.producer.put_events(all_events)

        # Update throughput metrics
        self.metrics.record_events_processed(result.get('success_count', 0))

        return result

    def ingest_stream(
        self,
        events: List[BaseEvent],
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingest a stream of events with automatic batching.

        Args:
            events: List of events
            batch_size: Batch size (defaults to settings)

        Returns:
            dict: Ingestion results
        """
        batch_size = batch_size or self.settings.batch_size

        total_success = 0
        total_failed = 0
        results = []

        # Process in batches
        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            result = self.producer.put_events(batch)

            total_success += result.get('success_count', 0)
            total_failed += result.get('failure_count', 0)
            results.append(result)

        logger.info(
            "Ingested event stream",
            total_events=len(events),
            total_success=total_success,
            total_failed=total_failed
        )

        return {
            "total_events": len(events),
            "total_success": total_success,
            "total_failed": total_failed,
            "batch_results": results
        }

    def create_match_event_batch(
        self,
        match_id: str,
        events: List[BaseEvent]
    ) -> EventBatch:
        """
        Create an event batch from a list of events.

        Args:
            match_id: Match identifier
            events: List of events

        Returns:
            EventBatch: Event batch
        """
        batch = EventBatch(
            batch_id=str(uuid.uuid4()),
            match_id=match_id,
            ingestion_time=datetime.utcnow(),
            total_events=len(events)
        )

        # Categorize events by type
        for event in events:
            if isinstance(event, MatchEvent):
                batch.match_events.append(event)
            elif isinstance(event, PlayerTrackingEvent):
                batch.tracking_events.append(event)
            elif isinstance(event, PhysiologicalEvent):
                batch.physiological_events.append(event)

        return batch
