"""
Metrics collection and tracking for performance evaluation.
"""

import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import statistics
from collections import defaultdict

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class LatencyMetrics:
    """Latency metrics container."""

    measurements: List[float] = field(default_factory=list)

    def add_measurement(self, latency_ms: float) -> None:
        """Add a latency measurement."""
        self.measurements.append(latency_ms)

    @property
    def count(self) -> int:
        """Number of measurements."""
        return len(self.measurements)

    @property
    def mean(self) -> float:
        """Mean latency."""
        if not self.measurements:
            return 0.0
        return statistics.mean(self.measurements)

    @property
    def median(self) -> float:
        """Median latency."""
        if not self.measurements:
            return 0.0
        return statistics.median(self.measurements)

    @property
    def p50(self) -> float:
        """50th percentile (median)."""
        return self.median

    @property
    def p95(self) -> float:
        """95th percentile."""
        if not self.measurements:
            return 0.0
        sorted_measurements = sorted(self.measurements)
        idx = int(len(sorted_measurements) * 0.95)
        return sorted_measurements[idx]

    @property
    def p99(self) -> float:
        """99th percentile."""
        if not self.measurements:
            return 0.0
        sorted_measurements = sorted(self.measurements)
        idx = int(len(sorted_measurements) * 0.99)
        return sorted_measurements[idx]

    @property
    def min(self) -> float:
        """Minimum latency."""
        if not self.measurements:
            return 0.0
        return min(self.measurements)

    @property
    def max(self) -> float:
        """Maximum latency."""
        if not self.measurements:
            return 0.0
        return max(self.measurements)

    @property
    def stddev(self) -> float:
        """Standard deviation."""
        if len(self.measurements) < 2:
            return 0.0
        return statistics.stdev(self.measurements)

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "p50": self.p50,
            "p95": self.p95,
            "p99": self.p99,
            "min": self.min,
            "max": self.max,
            "stddev": self.stddev,
        }


@dataclass
class ThroughputMetrics:
    """Throughput metrics container."""

    events_processed: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    def start(self) -> None:
        """Start throughput measurement."""
        self.start_time = time.time()

    def stop(self) -> None:
        """Stop throughput measurement."""
        self.end_time = time.time()

    def add_events(self, count: int) -> None:
        """Add processed events."""
        self.events_processed += count

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def events_per_second(self) -> float:
        """Events per second."""
        if self.duration_seconds == 0:
            return 0.0
        return self.events_processed / self.duration_seconds

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "events_processed": self.events_processed,
            "duration_seconds": self.duration_seconds,
            "events_per_second": self.events_per_second,
        }


@dataclass
class CostMetrics:
    """Cost tracking metrics."""

    # Lambda costs
    lambda_invocations: int = 0
    lambda_duration_ms: float = 0.0
    lambda_memory_mb: int = 512

    # Kinesis costs
    kinesis_put_records: int = 0
    kinesis_shard_hours: float = 0.0

    # DynamoDB costs
    dynamodb_read_units: int = 0
    dynamodb_write_units: int = 0

    # S3 costs
    s3_put_requests: int = 0
    s3_get_requests: int = 0
    s3_storage_gb: float = 0.0

    # API Gateway costs
    api_gateway_requests: int = 0
    websocket_messages: int = 0

    # Pricing (US East - can be configured)
    lambda_price_per_request: float = 0.0000002  # $0.20 per 1M requests
    lambda_price_per_gb_second: float = 0.0000166667  # $0.0000166667 per GB-second
    kinesis_price_per_shard_hour: float = 0.015  # $0.015 per shard hour
    kinesis_price_per_million_puts: float = 0.014  # $0.014 per million PUT units
    dynamodb_price_per_million_reads: float = 0.25  # $0.25 per million read units
    dynamodb_price_per_million_writes: float = 1.25  # $1.25 per million write units
    s3_price_per_1000_puts: float = 0.005  # $0.005 per 1000 PUT requests
    s3_price_per_1000_gets: float = 0.0004  # $0.0004 per 1000 GET requests
    api_gateway_price_per_million: float = 1.00  # $1.00 per million requests

    def calculate_lambda_cost(self) -> float:
        """Calculate Lambda costs."""
        request_cost = self.lambda_invocations * self.lambda_price_per_request
        gb_seconds = (self.lambda_memory_mb / 1024) * (self.lambda_duration_ms / 1000)
        compute_cost = gb_seconds * self.lambda_price_per_gb_second
        return request_cost + compute_cost

    def calculate_kinesis_cost(self) -> float:
        """Calculate Kinesis costs."""
        shard_cost = self.kinesis_shard_hours * self.kinesis_price_per_shard_hour
        put_cost = (self.kinesis_put_records / 1_000_000) * self.kinesis_price_per_million_puts
        return shard_cost + put_cost

    def calculate_dynamodb_cost(self) -> float:
        """Calculate DynamoDB costs."""
        read_cost = (self.dynamodb_read_units / 1_000_000) * self.dynamodb_price_per_million_reads
        write_cost = (self.dynamodb_write_units / 1_000_000) * self.dynamodb_price_per_million_writes
        return read_cost + write_cost

    def calculate_s3_cost(self) -> float:
        """Calculate S3 costs."""
        put_cost = (self.s3_put_requests / 1000) * self.s3_price_per_1000_puts
        get_cost = (self.s3_get_requests / 1000) * self.s3_price_per_1000_gets
        # Note: Storage costs would need to be added separately
        return put_cost + get_cost

    def calculate_api_gateway_cost(self) -> float:
        """Calculate API Gateway costs."""
        return ((self.api_gateway_requests + self.websocket_messages) / 1_000_000) * \
               self.api_gateway_price_per_million

    @property
    def total_cost(self) -> float:
        """Calculate total estimated cost."""
        return (
            self.calculate_lambda_cost() +
            self.calculate_kinesis_cost() +
            self.calculate_dynamodb_cost() +
            self.calculate_s3_cost() +
            self.calculate_api_gateway_cost()
        )

    @property
    def cost_per_event(self) -> float:
        """Calculate cost per event processed."""
        total_events = (
            self.kinesis_put_records +
            self.dynamodb_read_units +
            self.dynamodb_write_units
        )
        if total_events == 0:
            return 0.0
        return self.total_cost / total_events

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "lambda_cost_usd": self.calculate_lambda_cost(),
            "kinesis_cost_usd": self.calculate_kinesis_cost(),
            "dynamodb_cost_usd": self.calculate_dynamodb_cost(),
            "s3_cost_usd": self.calculate_s3_cost(),
            "api_gateway_cost_usd": self.calculate_api_gateway_cost(),
            "total_cost_usd": self.total_cost,
            "cost_per_event_usd": self.cost_per_event,
            "events_processed": self.kinesis_put_records,
        }


class MetricsCollector:
    """
    Central metrics collection system.
    Tracks latency, throughput, and cost metrics.
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.ingestion_latency = LatencyMetrics()
        self.processing_latency = LatencyMetrics()
        self.delivery_latency = LatencyMetrics()
        self.end_to_end_latency = LatencyMetrics()

        self.throughput = ThroughputMetrics()
        self.cost = CostMetrics()

        self._timers: Dict[str, float] = {}
        self._counters: Dict[str, int] = defaultdict(int)

    def start_timer(self, name: str) -> None:
        """
        Start a named timer.

        Args:
            name: Timer name
        """
        self._timers[name] = time.time()

    def stop_timer(self, name: str) -> Optional[float]:
        """
        Stop a named timer and return elapsed time.

        Args:
            name: Timer name

        Returns:
            float: Elapsed time in milliseconds, or None if timer not found
        """
        if name not in self._timers:
            logger.warning(f"Timer '{name}' not found")
            return None

        elapsed_ms = (time.time() - self._timers[name]) * 1000
        del self._timers[name]
        return elapsed_ms

    def record_latency(self, metric_type: str, latency_ms: float) -> None:
        """
        Record a latency measurement.

        Args:
            metric_type: Type of latency (ingestion, processing, delivery, end_to_end)
            latency_ms: Latency in milliseconds
        """
        if metric_type == "ingestion":
            self.ingestion_latency.add_measurement(latency_ms)
        elif metric_type == "processing":
            self.processing_latency.add_measurement(latency_ms)
        elif metric_type == "delivery":
            self.delivery_latency.add_measurement(latency_ms)
        elif metric_type == "end_to_end":
            self.end_to_end_latency.add_measurement(latency_ms)
        else:
            logger.warning(f"Unknown metric type: {metric_type}")

    def increment_counter(self, name: str, value: int = 1) -> None:
        """
        Increment a named counter.

        Args:
            name: Counter name
            value: Increment value
        """
        self._counters[name] += value

    def get_counter(self, name: str) -> int:
        """
        Get counter value.

        Args:
            name: Counter name

        Returns:
            int: Counter value
        """
        return self._counters.get(name, 0)

    def record_events_processed(self, count: int) -> None:
        """
        Record number of events processed.

        Args:
            count: Number of events
        """
        self.throughput.add_events(count)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive metrics summary.

        Returns:
            dict: Metrics summary
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "latency": {
                "ingestion": self.ingestion_latency.to_dict(),
                "processing": self.processing_latency.to_dict(),
                "delivery": self.delivery_latency.to_dict(),
                "end_to_end": self.end_to_end_latency.to_dict(),
            },
            "throughput": self.throughput.to_dict(),
            "cost": self.cost.to_dict(),
            "counters": dict(self._counters),
        }

    def reset(self) -> None:
        """Reset all metrics."""
        self.ingestion_latency = LatencyMetrics()
        self.processing_latency = LatencyMetrics()
        self.delivery_latency = LatencyMetrics()
        self.end_to_end_latency = LatencyMetrics()
        self.throughput = ThroughputMetrics()
        self.cost = CostMetrics()
        self._timers.clear()
        self._counters.clear()

    def meets_latency_target(self, target_ms: float = 500) -> bool:
        """
        Check if system meets latency target.

        Args:
            target_ms: Target latency in milliseconds

        Returns:
            bool: True if p95 latency is below target
        """
        return self.end_to_end_latency.p95 <= target_ms

    def meets_throughput_target(self, target_eps: float = 10000) -> bool:
        """
        Check if system meets throughput target.

        Args:
            target_eps: Target events per second

        Returns:
            bool: True if throughput meets or exceeds target
        """
        return self.throughput.events_per_second >= target_eps


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.

    Returns:
        MetricsCollector: Metrics collector
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector
