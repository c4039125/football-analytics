"""Logging configuration."""

import logging
import sys
from typing import Any, Dict
import structlog
from aws_lambda_powertools import Logger as PowertoolsLogger
from aws_lambda_powertools import Metrics, Tracer

from .config import get_settings


def setup_logging(level: str = None) -> None:
    """Configure logging."""
    settings = get_settings()
    log_level = level or settings.log_level

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.is_production
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get logger instance."""
    return structlog.get_logger(name)


class LambdaPowertoolsLogger:
    """
    Wrapper for AWS Lambda Powertools logger with additional features.
    """

    def __init__(self, service: str, level: str = None):
        """
        Initialize Lambda Powertools logger.

        Args:
            service: Service name
            level: Log level
        """
        settings = get_settings()
        log_level = level or settings.log_level

        self.logger = PowertoolsLogger(
            service=service,
            level=log_level,
        )
        self.metrics = Metrics(namespace="FootballAnalytics", service=service)
        self.tracer = Tracer(service=service) if settings.enable_xray else None

    def get_logger(self) -> PowertoolsLogger:
        """Get the Powertools logger instance."""
        return self.logger

    def get_metrics(self) -> Metrics:
        """Get the Metrics instance."""
        return self.metrics

    def get_tracer(self) -> Tracer:
        """Get the Tracer instance."""
        return self.tracer

    def add_context(self, **kwargs: Any) -> None:
        """
        Add context to all subsequent logs.

        Args:
            **kwargs: Context key-value pairs
        """
        for key, value in kwargs.items():
            self.logger.append_keys(**{key: value})

    def log_event(
        self,
        event_name: str,
        level: str = "INFO",
        **kwargs: Any
    ) -> None:
        """
        Log a structured event.

        Args:
            event_name: Event name
            level: Log level
            **kwargs: Event attributes
        """
        log_func = getattr(self.logger, level.lower())
        log_func(f"Event: {event_name}", extra=kwargs)

    def log_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count"
    ) -> None:
        """
        Log a metric.

        Args:
            metric_name: Metric name
            value: Metric value
            unit: Metric unit
        """
        self.metrics.add_metric(name=metric_name, unit=unit, value=value)


class ContextLogger:
    """
    Logger with automatic context propagation.
    """

    def __init__(self, logger: structlog.BoundLogger):
        """
        Initialize context logger.

        Args:
            logger: Base structlog logger
        """
        self._logger = logger
        self._context: Dict[str, Any] = {}

    def bind(self, **kwargs: Any) -> "ContextLogger":
        """
        Bind context to logger.

        Args:
            **kwargs: Context key-value pairs

        Returns:
            ContextLogger: Logger with bound context
        """
        new_logger = ContextLogger(self._logger.bind(**kwargs))
        new_logger._context = {**self._context, **kwargs}
        return new_logger

    def unbind(self, *keys: str) -> "ContextLogger":
        """
        Remove context keys.

        Args:
            *keys: Context keys to remove

        Returns:
            ContextLogger: Logger with removed keys
        """
        new_logger = ContextLogger(self._logger.unbind(*keys))
        new_context = {k: v for k, v in self._context.items() if k not in keys}
        new_logger._context = new_context
        return new_logger

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._logger.critical(message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, **kwargs)


def get_context_logger(name: str) -> ContextLogger:
    """
    Get a context-aware logger.

    Args:
        name: Logger name

    Returns:
        ContextLogger: Context-aware logger
    """
    base_logger = get_logger(name)
    return ContextLogger(base_logger)
