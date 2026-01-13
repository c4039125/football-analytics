"""
DynamoDB handler for storing and retrieving analytics data.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from boto3.dynamodb.conditions import Key, Attr

from ..models.event_models import BaseEvent, MatchEvent
from ..models.analytics_models import PlayerPerformanceMetrics, MatchStatistics
from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.aws_helpers import get_dynamodb_resource, batch_write_dynamodb
from ..utils.metrics import get_metrics_collector

logger = get_logger(__name__)


class DynamoDBHandler:
    """
    Low-level DynamoDB handler.
    Provides basic CRUD operations.
    """

    def __init__(self, table_name: Optional[str] = None):
        """
        Initialize DynamoDB handler.

        Args:
            table_name: DynamoDB table name (defaults to settings)
        """
        self.settings = get_settings()
        self.table_name = table_name or self.settings.dynamodb_table_name
        self.dynamodb = get_dynamodb_resource()
        self.table = self.dynamodb.Table(self.table_name)
        self.metrics = get_metrics_collector()

        logger.info(f"Initialized DynamoDB handler for table: {self.table_name}")

    def put_item(self, item: Dict[str, Any]) -> bool:
        """
        Put a single item to DynamoDB.

        Args:
            item: Item to store

        Returns:
            bool: True if successful
        """
        try:
            self.table.put_item(Item=item)
            self.metrics.cost.dynamodb_write_units += 1
            return True
        except Exception as e:
            logger.error(f"Failed to put item to DynamoDB", error=str(e), exc_info=True)
            return False

    def get_item(self, match_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single item from DynamoDB.

        Args:
            match_id: Match identifier
            event_id: Event identifier

        Returns:
            dict: Item data, or None if not found
        """
        try:
            response = self.table.get_item(
                Key={
                    'match_id': match_id,
                    'event_id': event_id
                }
            )
            self.metrics.cost.dynamodb_read_units += 1
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get item from DynamoDB", error=str(e))
            return None

    def query_by_match(self, match_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query all events for a specific match.

        Args:
            match_id: Match identifier
            limit: Maximum number of items to return

        Returns:
            list: List of items
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('match_id').eq(match_id),
                Limit=limit
            )
            self.metrics.cost.dynamodb_read_units += len(response.get('Items', []))
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to query DynamoDB by match", error=str(e))
            return []

    def query_by_player(
        self,
        player_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Query events for a specific player.

        Args:
            player_id: Player identifier
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of items

        Returns:
            list: List of items
        """
        try:
            key_condition = Key('player_id').eq(player_id)

            if start_time and end_time:
                key_condition = key_condition & Key('timestamp').between(
                    start_time.isoformat(),
                    end_time.isoformat()
                )

            response = self.table.query(
                IndexName='PlayerIndex',
                KeyConditionExpression=key_condition,
                Limit=limit
            )
            self.metrics.cost.dynamodb_read_units += len(response.get('Items', []))
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to query DynamoDB by player", error=str(e))
            return []

    def batch_write(self, items: List[Dict[str, Any]]) -> int:
        """
        Batch write items to DynamoDB.

        Args:
            items: List of items to write

        Returns:
            int: Number of items written
        """
        try:
            batch_write_dynamodb(self.table_name, items)
            self.metrics.cost.dynamodb_write_units += len(items)
            logger.info(f"Batch wrote {len(items)} items to DynamoDB")
            return len(items)
        except Exception as e:
            logger.error(f"Failed to batch write to DynamoDB", error=str(e))
            return 0

    def delete_item(self, match_id: str, event_id: str) -> bool:
        """
        Delete an item from DynamoDB.

        Args:
            match_id: Match identifier
            event_id: Event identifier

        Returns:
            bool: True if successful
        """
        try:
            self.table.delete_item(
                Key={
                    'match_id': match_id,
                    'event_id': event_id
                }
            )
            self.metrics.cost.dynamodb_write_units += 1
            return True
        except Exception as e:
            logger.error(f"Failed to delete item from DynamoDB", error=str(e))
            return False


class AnalyticsRepository:
    """
    High-level repository for analytics data.
    Provides domain-specific operations.
    """

    def __init__(self):
        """Initialize analytics repository."""
        self.db_handler = DynamoDBHandler()
        self.metrics = get_metrics_collector()

    def store_event(self, event: BaseEvent) -> bool:
        """
        Store an event in DynamoDB.

        Args:
            event: Event to store

        Returns:
            bool: True if successful
        """
        item = event.model_dump(mode='json')

        # Add DynamoDB-specific fields
        item['ttl'] = int((datetime.utcnow() + timedelta(days=30)).timestamp())
        item['created_at'] = datetime.utcnow().isoformat()

        return self.db_handler.put_item(item)

    def store_player_metrics(self, metrics: PlayerPerformanceMetrics) -> bool:
        """
        Store player performance metrics.

        Args:
            metrics: Player metrics

        Returns:
            bool: True if successful
        """
        item = metrics.model_dump(mode='json')

        # Add required keys
        item['match_id'] = metrics.match_id
        item['event_id'] = f"metrics_{metrics.player_id}_{uuid.uuid4().hex[:8]}"
        item['ttl'] = int((datetime.utcnow() + timedelta(days=90)).timestamp())
        item['created_at'] = datetime.utcnow().isoformat()
        item['event_type'] = 'player_metrics'

        return self.db_handler.put_item(item)

    def store_match_statistics(self, stats: MatchStatistics) -> bool:
        """
        Store match statistics.

        Args:
            stats: Match statistics

        Returns:
            bool: True if successful
        """
        item = stats.model_dump(mode='json')

        # Add required keys
        item['match_id'] = stats.match_id
        item['event_id'] = f"stats_{uuid.uuid4().hex[:8]}"
        item['ttl'] = int((datetime.utcnow() + timedelta(days=365)).timestamp())
        item['created_at'] = datetime.utcnow().isoformat()
        item['event_type'] = 'match_statistics'

        return self.db_handler.put_item(item)

    def get_match_events(self, match_id: str) -> List[Dict[str, Any]]:
        """
        Get all events for a match.

        Args:
            match_id: Match identifier

        Returns:
            list: List of events
        """
        return self.db_handler.query_by_match(match_id)

    def get_player_metrics(
        self,
        player_id: str,
        match_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get player metrics.

        Args:
            player_id: Player identifier
            match_id: Optional match filter

        Returns:
            list: List of metrics
        """
        metrics = self.db_handler.query_by_player(player_id)

        if match_id:
            metrics = [m for m in metrics if m.get('match_id') == match_id]

        return metrics

    def store_events_batch(self, events: List[BaseEvent]) -> int:
        """
        Store multiple events in a batch.

        Args:
            events: List of events

        Returns:
            int: Number of events stored
        """
        items = []
        for event in events:
            item = event.model_dump(mode='json')
            item['ttl'] = int((datetime.utcnow() + timedelta(days=30)).timestamp())
            item['created_at'] = datetime.utcnow().isoformat()
            items.append(item)

        return self.db_handler.batch_write(items)

    def get_recent_matches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent matches.

        Args:
            limit: Number of matches to retrieve

        Returns:
            list: List of recent matches
        """
        # This would typically involve a scan with filters
        # For production, consider using a GSI for recent matches
        try:
            response = self.db_handler.table.scan(
                FilterExpression=Attr('event_type').eq('match_statistics'),
                Limit=limit
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to get recent matches", error=str(e))
            return []
