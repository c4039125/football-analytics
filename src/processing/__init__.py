"""
Processing layer for football analytics.
Lambda functions for event processing.
"""

from .event_processor import EventProcessor
from .analytics_engine import AnalyticsEngine
from .threat_analyzer import ThreatAnalyzer

__all__ = [
    "EventProcessor",
    "AnalyticsEngine",
    "ThreatAnalyzer",
]
