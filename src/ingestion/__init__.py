"""Data ingestion layer for football analytics."""

from .kinesis_producer import KinesisProducer, EventIngestionService
from .nigerian_football_data import NigerianFootballDataFetcher, NigerianLeague

__all__ = [
    "KinesisProducer",
    "EventIngestionService",
    "NigerianFootballDataFetcher",
    "NigerianLeague",
]
