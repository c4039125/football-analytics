"""
Event processor for Lambda functions.
Processes incoming events from Kinesis and generates analytics.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from models.event_models import BaseEvent, MatchEvent, PlayerTrackingEvent
from models.analytics_models import PlayerPerformanceMetrics, ThreatAssessment
from utils.logger import get_logger
from utils.metrics import get_metrics_collector
from utils.config import get_settings

logger = get_logger(__name__)


class EventProcessor:
    """
    Main event processor for Lambda functions.
    Processes events from Kinesis stream.
    """

    def __init__(self):
        """Initialize event processor."""
        self.settings = get_settings()
        self.metrics = get_metrics_collector()
        logger.info("Event processor initialized")

    def process_kinesis_record(self, record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single Kinesis record.

        Args:
            record: Kinesis record

        Returns:
            dict: Processing result, or None if processing failed
        """
        try:
            self.metrics.start_timer('processing')

            # Decode record data
            import base64
            data = base64.b64decode(record['kinesis']['data'])
            event_data = json.loads(data)

            # Determine event type and process accordingly
            event_type = event_data.get('event_type')

            if event_type in ['pass', 'shot', 'tackle', 'goal']:
                result = self.process_match_event(event_data)
            elif event_type == 'player_position':
                result = self.process_tracking_event(event_data)
            else:
                result = self.process_generic_event(event_data)

            latency_ms = self.metrics.stop_timer('processing')
            self.metrics.record_latency('processing', latency_ms)

            # Update cost metrics
            self.metrics.cost.lambda_invocations += 1
            self.metrics.cost.lambda_duration_ms += latency_ms

            logger.debug(
                "Processed Kinesis record",
                event_id=event_data.get('event_id'),
                event_type=event_type,
                processing_time_ms=latency_ms
            )

            return result

        except Exception as e:
            logger.error(
                "Failed to process Kinesis record",
                error=str(e),
                exc_info=True
            )
            self.metrics.increment_counter('processing_errors')
            return None

    def process_match_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a match event (pass, shot, etc.).

        Args:
            event_data: Event data

        Returns:
            dict: Processing result
        """
        logger.debug(
            "Processing match event",
            event_id=event_data.get('event_id'),
            event_type=event_data.get('event_type')
        )

        # Extract relevant information
        result = {
            'event_id': event_data.get('event_id'),
            'match_id': event_data.get('match_id'),
            'event_type': event_data.get('event_type'),
            'player_id': event_data.get('player_id'),
            'team_id': event_data.get('team_id'),
            'timestamp': event_data.get('timestamp'),
            'outcome': event_data.get('outcome'),
            'processed_at': datetime.utcnow().isoformat()
        }

        # Add computed metrics
        if event_data.get('event_type') == 'shot':
            result['xg'] = self._calculate_xg(event_data)
        elif event_data.get('event_type') == 'pass':
            result['pass_success_probability'] = self._calculate_pass_success(event_data)

        self.metrics.increment_counter('match_events_processed')

        return result

    def process_tracking_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a player tracking event.

        Args:
            event_data: Event data

        Returns:
            dict: Processing result
        """
        result = {
            'event_id': event_data.get('event_id'),
            'match_id': event_data.get('match_id'),
            'player_id': event_data.get('player_id'),
            'position': event_data.get('position'),
            'velocity': event_data.get('velocity'),
            'frame_id': event_data.get('frame_id'),
            'processed_at': datetime.utcnow().isoformat()
        }

        self.metrics.increment_counter('tracking_events_processed')

        return result

    def process_generic_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a generic event.

        Args:
            event_data: Event data

        Returns:
            dict: Processing result
        """
        result = {
            'event_id': event_data.get('event_id'),
            'match_id': event_data.get('match_id'),
            'event_type': event_data.get('event_type'),
            'processed_at': datetime.utcnow().isoformat()
        }

        self.metrics.increment_counter('generic_events_processed')

        return result

    def _calculate_xg(self, event_data: Dict[str, Any]) -> float:
        """
        Calculate expected goals (xG) for a shot.
        Simplified model based on distance and angle.

        Args:
            event_data: Event data

        Returns:
            float: xG value (0-1)
        """
        import math

        position = event_data.get('position', {})
        x = position.get('x', 60)
        y = position.get('y', 40)

        # Goal position (center of goal at x=120, y=40)
        goal_x, goal_y = 120, 40

        # Calculate distance to goal
        distance = math.sqrt((goal_x - x) ** 2 + (goal_y - y) ** 2)

        # Calculate angle to goal (simplified)
        angle = abs(math.atan2(goal_y - y, goal_x - x))

        # Simplified xG model (logistic regression approximation)
        # Real models use machine learning with more features
        xg = 1 / (1 + math.exp(0.1 * distance - 3 + 0.5 * angle))

        return min(max(xg, 0.0), 1.0)

    def _calculate_pass_success(self, event_data: Dict[str, Any]) -> float:
        """
        Calculate pass success probability.

        Args:
            event_data: Event data

        Returns:
            float: Success probability (0-1)
        """
        import math

        position = event_data.get('position', {})
        end_position = event_data.get('end_position', {})

        if not position or not end_position:
            return 0.5  # Default

        # Calculate pass distance
        x1, y1 = position.get('x', 0), position.get('y', 0)
        x2, y2 = end_position.get('x', 0), end_position.get('y', 0)

        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

        # Simple model: shorter passes have higher success rate
        success_prob = 1 / (1 + 0.02 * distance)

        return min(max(success_prob, 0.0), 1.0)

    def process_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of Kinesis records.

        Args:
            records: List of Kinesis records

        Returns:
            dict: Batch processing result
        """
        self.metrics.start_timer('batch_processing')

        results = []
        errors = []

        for record in records:
            try:
                result = self.process_kinesis_record(record)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error("Error processing record", error=str(e))
                errors.append({
                    'record_id': record.get('eventID'),
                    'error': str(e)
                })

        latency_ms = self.metrics.stop_timer('batch_processing')

        return {
            'processed_count': len(results),
            'error_count': len(errors),
            'results': results,
            'errors': errors,
            'processing_time_ms': latency_ms
        }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: Lambda event (Kinesis records)
        context: Lambda context

    Returns:
        dict: Lambda response
    """
    processor = EventProcessor()

    try:
        records = event.get('Records', [])
        logger.info(f"Processing {len(records)} Kinesis records")

        result = processor.process_batch(records)

        logger.info(
            "Batch processing complete",
            processed=result['processed_count'],
            errors=result['error_count']
        )

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        logger.error("Lambda execution failed", error=str(e), exc_info=True)

        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
