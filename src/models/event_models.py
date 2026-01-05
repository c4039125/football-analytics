"""Event data models for football analytics."""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, validator, constr, confloat, conint


class EventType(str, Enum):
    """Match event types."""

    # Match Events
    GOAL = "goal"
    SHOT = "shot"
    PASS = "pass"
    TACKLE = "tackle"
    FOUL = "foul"
    CARD_YELLOW = "card_yellow"
    CARD_RED = "card_red"
    SUBSTITUTION = "substitution"
    CORNER = "corner"
    FREE_KICK = "free_kick"
    PENALTY = "penalty"
    OFFSIDE = "offside"

    # Tracking Events
    PLAYER_POSITION = "player_position"
    BALL_POSITION = "ball_position"

    # Physiological Events
    HEART_RATE = "heart_rate"
    DISTANCE_COVERED = "distance_covered"
    SPRINT = "sprint"
    FATIGUE_INDICATOR = "fatigue_indicator"


class BaseEvent(BaseModel):
    """Base event model."""

    event_id: str = Field(..., description="Event ID")
    match_id: str = Field(..., description="Match ID")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_type: EventType = Field(..., description="Event type")
    ingestion_time: Optional[datetime] = Field(default=None, description="Ingestion time")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True


class Position(BaseModel):
    """Pitch position."""

    x: confloat(ge=0.0, le=120.0) = Field(..., description="X coordinate")
    y: confloat(ge=0.0, le=80.0) = Field(..., description="Y coordinate")


class Velocity(BaseModel):
    """Velocity vector."""

    vx: float = Field(..., description="X velocity")
    vy: float = Field(..., description="Y velocity")
    speed: confloat(ge=0.0) = Field(..., description="Speed")


class MatchEvent(BaseEvent):
    """Match event model."""

    period: conint(ge=1, le=5) = Field(..., description="Period")
    minute: conint(ge=0, le=120) = Field(..., description="Minute")
    second: conint(ge=0, le=59) = Field(..., description="Second")

    team_id: str = Field(..., description="Team ID")
    team_name: str = Field(..., description="Team name")

    player_id: Optional[str] = Field(None, description="Player ID")
    player_name: Optional[str] = Field(None, description="Player name")

    position: Optional[Position] = Field(None, description="Position")
    end_position: Optional[Position] = Field(None, description="End position")

    outcome: Optional[str] = Field(None, description="Outcome")
    possession_team_id: Optional[str] = Field(None, description="Possession team")

    related_events: List[str] = Field(default_factory=list, description="Related events")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")

    @validator('second')
    def validate_second(cls, v, values):
        if 'minute' in values and values['minute'] == 120:
            return v
        return v


class PlayerTrackingEvent(BaseEvent):
    """Player tracking data (25 Hz)."""

    player_id: str = Field(..., description="Player ID")
    team_id: str = Field(..., description="Team ID")
    jersey_number: conint(ge=1, le=99) = Field(..., description="Jersey number")

    position: Position = Field(..., description="Position")
    velocity: Optional[Velocity] = Field(None, description="Velocity")

    period: conint(ge=1, le=5) = Field(..., description="Period")
    frame_id: int = Field(..., description="Frame ID")

    acceleration: Optional[float] = Field(None, description="Acceleration")
    direction: Optional[confloat(ge=0.0, lt=360.0)] = Field(None, description="Direction")

    in_possession: bool = Field(default=False, description="In possession")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class PhysiologicalEvent(BaseEvent):
    """Physiological metrics from wearables."""

    player_id: str = Field(..., description="Player ID")
    team_id: str = Field(..., description="Team ID")

    heart_rate: Optional[conint(ge=40, le=220)] = Field(None, description="Heart rate")
    heart_rate_variability: Optional[float] = Field(None, description="HRV")

    distance_covered: Optional[confloat(ge=0.0)] = Field(None, description="Distance")
    high_intensity_distance: Optional[confloat(ge=0.0)] = Field(None, description="HI distance")
    sprint_distance: Optional[confloat(ge=0.0)] = Field(None, description="Sprint distance")

    player_load: Optional[confloat(ge=0.0)] = Field(None, description="Player load")
    fatigue_index: Optional[confloat(ge=0.0, le=1.0)] = Field(None, description="Fatigue")

    max_speed: Optional[confloat(ge=0.0)] = Field(None, description="Max speed")
    avg_speed: Optional[confloat(ge=0.0)] = Field(None, description="Avg speed")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class BallTrackingEvent(BaseEvent):
    """Ball tracking data."""

    position: Position = Field(..., description="Position")
    velocity: Optional[Velocity] = Field(None, description="Velocity")

    period: conint(ge=1, le=5) = Field(..., description="Period")
    frame_id: int = Field(..., description="Frame ID")

    height: Optional[confloat(ge=0.0)] = Field(None, description="Height")
    possession_team_id: Optional[str] = Field(None, description="Possession team")
    possession_player_id: Optional[str] = Field(None, description="Possession player")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")


class EventBatch(BaseModel):
    """Event batch for efficient processing."""

    batch_id: str = Field(..., description="Batch ID")
    match_id: str = Field(..., description="Match ID")
    ingestion_time: datetime = Field(..., description="Ingestion time")

    match_events: List[MatchEvent] = Field(default_factory=list)
    tracking_events: List[PlayerTrackingEvent] = Field(default_factory=list)
    physiological_events: List[PhysiologicalEvent] = Field(default_factory=list)
    ball_tracking_events: List[BallTrackingEvent] = Field(default_factory=list)

    total_events: int = Field(..., description="Total events")

    @validator('total_events', always=True)
    def validate_total_events(cls, v, values):
        total = (
            len(values.get('match_events', [])) +
            len(values.get('tracking_events', [])) +
            len(values.get('physiological_events', [])) +
            len(values.get('ball_tracking_events', []))
        )
        return total

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
