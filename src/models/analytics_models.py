"""Analytics and computed metrics models."""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, confloat, conint
from enum import Enum


class PlayerRole(str, Enum):
    """Player positional roles."""

    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"
    WING_BACK = "wing_back"
    DEFENSIVE_MIDFIELDER = "defensive_midfielder"
    ATTACKING_MIDFIELDER = "attacking_midfielder"
    WINGER = "winger"
    STRIKER = "striker"


class DefensiveActionType(str, Enum):
    """Types of defensive actions."""

    TACKLE = "tackle"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    BLOCK = "block"
    PRESSURE = "pressure"
    AERIAL_DUEL = "aerial_duel"


class ThreatLevel(str, Enum):
    """Threat level classification."""

    CRITICAL = "critical"  # > 0.8
    HIGH = "high"  # 0.6 - 0.8
    MEDIUM = "medium"  # 0.4 - 0.6
    LOW = "low"  # 0.2 - 0.4
    MINIMAL = "minimal"  # < 0.2


class PlayerPerformanceMetrics(BaseModel):
    """
    Comprehensive player performance metrics.
    Based on PlayeRank and similar multi-dimensional evaluation frameworks.
    """

    player_id: str = Field(..., description="Player identifier")
    player_name: str = Field(..., description="Player name")
    team_id: str = Field(..., description="Team identifier")
    match_id: str = Field(..., description="Match identifier")
    timestamp: datetime = Field(..., description="Metrics computation timestamp")

    role: PlayerRole = Field(..., description="Player role/position")

    # Offensive metrics
    goals: conint(ge=0) = Field(default=0, description="Goals scored")
    assists: conint(ge=0) = Field(default=0, description="Assists provided")
    shots: conint(ge=0) = Field(default=0, description="Total shots")
    shots_on_target: conint(ge=0) = Field(default=0, description="Shots on target")
    expected_goals: confloat(ge=0.0) = Field(default=0.0, description="Expected goals (xG)")
    expected_assists: confloat(ge=0.0) = Field(default=0.0, description="Expected assists (xA)")

    # Passing metrics
    passes_completed: conint(ge=0) = Field(default=0, description="Completed passes")
    passes_attempted: conint(ge=0) = Field(default=0, description="Attempted passes")
    pass_accuracy: confloat(ge=0.0, le=1.0) = Field(default=0.0, description="Pass accuracy")
    key_passes: conint(ge=0) = Field(default=0, description="Key passes")
    progressive_passes: conint(ge=0) = Field(default=0, description="Progressive passes")

    # Defensive metrics
    tackles_won: conint(ge=0) = Field(default=0, description="Tackles won")
    tackles_attempted: conint(ge=0) = Field(default=0, description="Tackles attempted")
    interceptions: conint(ge=0) = Field(default=0, description="Interceptions")
    clearances: conint(ge=0) = Field(default=0, description="Clearances")
    blocks: conint(ge=0) = Field(default=0, description="Blocks")
    defensive_actions_value: confloat(ge=0.0) = Field(
        default=0.0,
        description="DAxT value (Defensive Action Expected Threat)"
    )

    # Physical metrics
    distance_covered: confloat(ge=0.0) = Field(default=0.0, description="Distance covered (m)")
    high_intensity_distance: confloat(ge=0.0) = Field(
        default=0.0,
        description="High intensity running (m)"
    )
    sprints: conint(ge=0) = Field(default=0, description="Number of sprints")
    max_speed: confloat(ge=0.0) = Field(default=0.0, description="Maximum speed (m/s)")

    # Possession metrics
    touches: conint(ge=0) = Field(default=0, description="Total touches")
    possession_won: conint(ge=0) = Field(default=0, description="Times won possession")
    possession_lost: conint(ge=0) = Field(default=0, description="Times lost possession")
    dribbles_successful: conint(ge=0) = Field(default=0, description="Successful dribbles")
    dribbles_attempted: conint(ge=0) = Field(default=0, description="Attempted dribbles")

    # Overall rating
    performance_score: confloat(ge=0.0, le=10.0) = Field(
        default=5.0,
        description="Overall performance score (0-10)"
    )

    # Context
    minutes_played: confloat(ge=0.0) = Field(default=0.0, description="Minutes played")
    fatigue_level: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Current fatigue level"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DefensiveAction(BaseModel):
    """
    Defensive action with threat mitigation value (DAxT model).
    Based on Merhej et al. (2021) research.
    """

    action_id: str = Field(..., description="Unique action identifier")
    match_id: str = Field(..., description="Match identifier")
    timestamp: datetime = Field(..., description="Action timestamp")

    player_id: str = Field(..., description="Defending player ID")
    team_id: str = Field(..., description="Defending team ID")

    action_type: DefensiveActionType = Field(..., description="Type of defensive action")

    # Positional context
    position_x: confloat(ge=0.0, le=120.0) = Field(..., description="X position")
    position_y: confloat(ge=0.0, le=80.0) = Field(..., description="Y position")

    # Threat assessment
    threat_before: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Threat value before action"
    )
    threat_after: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Threat value after action"
    )
    threat_reduction: confloat(ge=-1.0, le=1.0) = Field(
        ...,
        description="Threat reduction (DAxT value)"
    )

    # Action outcome
    successful: bool = Field(..., description="Whether action was successful")
    possession_regained: bool = Field(..., description="Whether possession was regained")

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreatAssessment(BaseModel):
    """
    Real-time threat assessment for a match situation.
    Calculates the probability of a goal being scored in the current situation.
    """

    assessment_id: str = Field(..., description="Unique assessment identifier")
    match_id: str = Field(..., description="Match identifier")
    timestamp: datetime = Field(..., description="Assessment timestamp")

    attacking_team_id: str = Field(..., description="Attacking team ID")
    defending_team_id: str = Field(..., description="Defending team ID")

    # Ball position
    ball_x: confloat(ge=0.0, le=120.0) = Field(..., description="Ball X position")
    ball_y: confloat(ge=0.0, le=80.0) = Field(..., description="Ball Y position")

    # Threat metrics
    threat_value: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Overall threat value (0-1)"
    )
    threat_level: ThreatLevel = Field(..., description="Categorical threat level")

    expected_goal_value: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Expected goal value for current situation"
    )

    # Contextual factors
    distance_to_goal: confloat(ge=0.0) = Field(..., description="Distance to goal (m)")
    angle_to_goal: confloat(ge=0.0, le=180.0) = Field(..., description="Angle to goal (degrees)")
    defenders_nearby: conint(ge=0) = Field(..., description="Number of nearby defenders")
    attackers_nearby: conint(ge=0) = Field(..., description="Number of nearby attackers")

    # Recommendations
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Recommended defensive actions"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FormationPosition(BaseModel):
    """Player position in team formation."""

    player_id: str = Field(..., description="Player identifier")
    jersey_number: conint(ge=1, le=99) = Field(..., description="Jersey number")
    role: PlayerRole = Field(..., description="Player role")

    # Average position
    avg_x: confloat(ge=0.0, le=120.0) = Field(..., description="Average X position")
    avg_y: confloat(ge=0.0, le=80.0) = Field(..., description="Average Y position")

    # Position variance (movement freedom)
    std_x: confloat(ge=0.0) = Field(..., description="Standard deviation X")
    std_y: confloat(ge=0.0) = Field(..., description="Standard deviation Y")


class TeamFormation(BaseModel):
    """
    Team formation analysis.
    Identifies tactical shape and player positioning patterns.
    """

    formation_id: str = Field(..., description="Unique formation identifier")
    match_id: str = Field(..., description="Match identifier")
    team_id: str = Field(..., description="Team identifier")
    timestamp: datetime = Field(..., description="Analysis timestamp")

    # Formation identification
    formation_name: str = Field(..., description="Formation name (e.g., 4-3-3, 4-4-2)")
    confidence: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Confidence in formation detection"
    )

    # Player positions
    player_positions: List[FormationPosition] = Field(
        ...,
        description="Player positions in formation"
    )

    # Formation metrics
    compactness: confloat(ge=0.0, le=1.0) = Field(
        ...,
        description="Team compactness (0=spread out, 1=very compact)"
    )
    width: confloat(ge=0.0) = Field(..., description="Team width (m)")
    depth: confloat(ge=0.0) = Field(..., description="Team depth (m)")

    # Centroid
    centroid_x: confloat(ge=0.0, le=120.0) = Field(..., description="Formation centroid X")
    centroid_y: confloat(ge=0.0, le=80.0) = Field(..., description="Formation centroid Y")

    # Tactical insights
    defensive_line: confloat(ge=0.0, le=120.0) = Field(
        ...,
        description="Defensive line X position"
    )
    offensive_line: confloat(ge=0.0, le=120.0) = Field(
        ...,
        description="Offensive line X position"
    )

    pressing_intensity: confloat(ge=0.0, le=1.0) = Field(
        default=0.0,
        description="Pressing intensity (0-1)"
    )

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MatchStatistics(BaseModel):
    """
    Aggregated match statistics.
    """

    match_id: str = Field(..., description="Match identifier")
    timestamp: datetime = Field(..., description="Statistics timestamp")

    home_team_id: str = Field(..., description="Home team ID")
    away_team_id: str = Field(..., description="Away team ID")

    # Score
    home_score: conint(ge=0) = Field(default=0)
    away_score: conint(ge=0) = Field(default=0)

    # Possession
    home_possession: confloat(ge=0.0, le=1.0) = Field(default=0.5)
    away_possession: confloat(ge=0.0, le=1.0) = Field(default=0.5)

    # Shots
    home_shots: conint(ge=0) = Field(default=0)
    away_shots: conint(ge=0) = Field(default=0)
    home_shots_on_target: conint(ge=0) = Field(default=0)
    away_shots_on_target: conint(ge=0) = Field(default=0)

    # Expected goals
    home_xg: confloat(ge=0.0) = Field(default=0.0)
    away_xg: confloat(ge=0.0) = Field(default=0.0)

    # Passing
    home_passes: conint(ge=0) = Field(default=0)
    away_passes: conint(ge=0) = Field(default=0)
    home_pass_accuracy: confloat(ge=0.0, le=1.0) = Field(default=0.0)
    away_pass_accuracy: confloat(ge=0.0, le=1.0) = Field(default=0.0)

    # Distance covered
    home_distance: confloat(ge=0.0) = Field(default=0.0)
    away_distance: confloat(ge=0.0) = Field(default=0.0)

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
