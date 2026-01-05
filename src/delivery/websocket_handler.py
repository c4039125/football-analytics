"""
WebSocket handler for real-time analytics delivery.
Lambda function handler for API Gateway WebSocket.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.response_models import AnalyticsResponse
from ..storage.dynamodb_handler import AnalyticsRepository
from ..utils.config import get_settings
from ..utils.logger import get_logger
from ..utils.aws_helpers import get_dynamodb_resource, get_api_gateway_client

logger = get_logger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections.
    Stores connection info in DynamoDB.
    """

    def __init__(self):
        """Initialize connection manager."""
        self.settings = get_settings()
        self.dynamodb = get_dynamodb_resource()
        self.table_name = f"{self.settings.dynamodb_table_name}-connections"

    def add_connection(self, connection_id: str, match_id: Optional[str] = None) -> bool:
        """
        Add a WebSocket connection.

        Args:
            connection_id: Connection ID
            match_id: Optional match to subscribe to

        Returns:
            bool: True if successful
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            table.put_item(
                Item={
                    'connection_id': connection_id,
                    'match_id': match_id or 'all',
                    'connected_at': datetime.utcnow().isoformat(),
                    'ttl': int((datetime.utcnow().timestamp()) + 3600)  # 1 hour TTL
                }
            )
            logger.info(f"Added WebSocket connection", connection_id=connection_id)
            return True
        except Exception as e:
            logger.error(f"Failed to add connection", error=str(e))
            return False

    def remove_connection(self, connection_id: str) -> bool:
        """
        Remove a WebSocket connection.

        Args:
            connection_id: Connection ID

        Returns:
            bool: True if successful
        """
        try:
            table = self.dynamodb.Table(self.table_name)
            table.delete_item(
                Key={'connection_id': connection_id}
            )
            logger.info(f"Removed WebSocket connection", connection_id=connection_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove connection", error=str(e))
            return False

    def get_connections(self, match_id: Optional[str] = None) -> List[str]:
        """
        Get all active connections, optionally filtered by match.

        Args:
            match_id: Optional match filter

        Returns:
            list: List of connection IDs
        """
        try:
            table = self.dynamodb.Table(self.table_name)

            if match_id:
                response = table.query(
                    IndexName='MatchIndex',
                    KeyConditionExpression='match_id = :match_id',
                    ExpressionAttributeValues={':match_id': match_id}
                )
            else:
                response = table.scan()

            return [item['connection_id'] for item in response.get('Items', [])]
        except Exception as e:
            logger.error(f"Failed to get connections", error=str(e))
            return []


class WebSocketHandler:
    """
    WebSocket handler for real-time data delivery.
    """

    def __init__(self, api_gateway_endpoint: Optional[str] = None):
        """
        Initialize WebSocket handler.

        Args:
            api_gateway_endpoint: API Gateway endpoint
        """
        self.settings = get_settings()
        self.endpoint = api_gateway_endpoint or self.settings.websocket_endpoint
        self.connection_manager = ConnectionManager()
        self.repository = AnalyticsRepository()

        if self.endpoint:
            self.api_gateway_client = get_api_gateway_client()

    def send_message(
        self,
        connection_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a WebSocket connection.

        Args:
            connection_id: Connection ID
            data: Data to send

        Returns:
            bool: True if successful
        """
        try:
            self.api_gateway_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps(data).encode('utf-8')
            )
            logger.debug(f"Sent message to connection", connection_id=connection_id)
            return True
        except Exception as e:
            logger.error(f"Failed to send message", connection_id=connection_id, error=str(e))
            # Connection might be stale, remove it
            self.connection_manager.remove_connection(connection_id)
            return False

    def broadcast_analytics(
        self,
        analytics: AnalyticsResponse,
        match_id: Optional[str] = None
    ) -> int:
        """
        Broadcast analytics to all connected clients.

        Args:
            analytics: Analytics data to broadcast
            match_id: Optional match filter

        Returns:
            int: Number of successful broadcasts
        """
        connections = self.connection_manager.get_connections(match_id)
        success_count = 0

        message = analytics.model_dump(mode='json')

        for connection_id in connections:
            if self.send_message(connection_id, message):
                success_count += 1

        logger.info(
            f"Broadcast analytics",
            total_connections=len(connections),
            successful=success_count
        )

        return success_count


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for WebSocket events.

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        dict: Lambda response
    """
    route_key = event.get('requestContext', {}).get('routeKey')
    connection_id = event.get('requestContext', {}).get('connectionId')

    handler = WebSocketHandler()

    try:
        if route_key == '$connect':
            # Handle connection
            query_params = event.get('queryStringParameters', {})
            match_id = query_params.get('match_id')

            handler.connection_manager.add_connection(connection_id, match_id)

            return {'statusCode': 200}

        elif route_key == '$disconnect':
            # Handle disconnection
            handler.connection_manager.remove_connection(connection_id)

            return {'statusCode': 200}

        elif route_key == '$default':
            # Handle default route (messages from client)
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')

            if action == 'subscribe':
                match_id = body.get('match_id')
                handler.connection_manager.add_connection(connection_id, match_id)

                response = {
                    'action': 'subscribed',
                    'match_id': match_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
                handler.send_message(connection_id, response)

            elif action == 'ping':
                response = {
                    'action': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                }
                handler.send_message(connection_id, response)

            return {'statusCode': 200}

        else:
            logger.warning(f"Unknown route key", route_key=route_key)
            return {'statusCode': 400}

    except Exception as e:
        logger.error(f"WebSocket handler error", error=str(e), exc_info=True)
        return {'statusCode': 500}
