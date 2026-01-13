"""API response models."""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Status")
    timestamp: datetime = Field(..., description="Timestamp")
    version: str = Field(..., description="Version")
    service: str = Field(..., description="Service")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependencies")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsResponse(BaseModel):
    """Performance metrics response."""

    request_id: str = Field(..., description="Request ID")
    timestamp: datetime = Field(..., description="Timestamp")

    ingestion_latency_ms: Optional[float] = Field(None, description="Ingestion latency")
    processing_latency_ms: Optional[float] = Field(None, description="Processing latency")
    delivery_latency_ms: Optional[float] = Field(None, description="Delivery latency")
    end_to_end_latency_ms: Optional[float] = Field(None, description="Total latency")

    events_processed: int = Field(default=0, description="Events processed")
    events_per_second: Optional[float] = Field(None, description="Events per second")

    memory_used_mb: Optional[float] = Field(None, description="Memory used")
    cpu_time_ms: Optional[float] = Field(None, description="CPU time")

    estimated_cost_usd: Optional[float] = Field(None, description="Est. cost")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalyticsResponse(BaseModel):
    """Generic analytics response wrapper."""

    request_id: str = Field(..., description="Request identifier")
    match_id: str = Field(..., description="Match identifier")
    timestamp: datetime = Field(..., description="Response timestamp")

    analytics_type: str = Field(..., description="Type of analytics returned")
    data: Dict[str, Any] = Field(..., description="Analytics data")

    # Performance metrics
    processing_time_ms: float = Field(..., description="Processing time (ms)")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    request_id: Optional[str] = Field(None, description="Request identifier")
    timestamp: datetime = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BatchProcessingResponse(BaseModel):
    """Response for batch processing operations."""

    batch_id: str = Field(..., description="Batch identifier")
    status: str = Field(..., description="Processing status")
    timestamp: datetime = Field(..., description="Response timestamp")

    total_events: int = Field(..., description="Total events in batch")
    processed_events: int = Field(..., description="Successfully processed events")
    failed_events: int = Field(default=0, description="Failed events")

    processing_time_ms: float = Field(..., description="Total processing time (ms)")

    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of errors encountered"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
