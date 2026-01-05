"""Threat analyzer using DAxT model."""

import math
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.event_models import MatchEvent, PlayerTrackingEvent, Position
from ..models.analytics_models import (
    ThreatAssessment,
    ThreatLevel,
    DefensiveAction,
    DefensiveActionType,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThreatAnalyzer:
    """Threat analyzer using DAxT model."""

    def __init__(self):
        logger.info("Threat analyzer initialized")

    def assess_threat(
        self,
        match_id: str,
        ball_position: Position,
        attacking_team_id: str,
        defending_team_id: str,
        attacking_players: List[PlayerTrackingEvent],
        defending_players: List[PlayerTrackingEvent]
    ) -> ThreatAssessment:
        """Assess current threat level."""
        # Calculate distance and angle to goal
        goal_position = Position(x=120.0, y=40.0)
        distance_to_goal = self._calculate_distance(ball_position, goal_position)
        angle_to_goal = self._calculate_angle_to_goal(ball_position)

        # Count nearby players
        defenders_nearby = self._count_nearby_players(
            ball_position,
            defending_players,
            radius=10.0
        )
        attackers_nearby = self._count_nearby_players(
            ball_position,
            attacking_players,
            radius=10.0
        )

        # Calculate threat value using spatial model
        threat_value = self._calculate_threat_value(
            ball_position,
            distance_to_goal,
            angle_to_goal,
            defenders_nearby,
            attackers_nearby
        )

        # Determine threat level category
        threat_level = self._categorize_threat(threat_value)

        # Calculate expected goal value
        xg_value = self._calculate_xg_from_position(
            ball_position,
            distance_to_goal,
            angle_to_goal
        )

        # Generate recommendations
        recommendations = self._generate_defensive_recommendations(
            threat_level,
            defenders_nearby,
            attackers_nearby,
            ball_position
        )

        assessment = ThreatAssessment(
            assessment_id=str(uuid.uuid4()),
            match_id=match_id,
            timestamp=datetime.utcnow(),
            attacking_team_id=attacking_team_id,
            defending_team_id=defending_team_id,
            ball_x=ball_position.x,
            ball_y=ball_position.y,
            threat_value=threat_value,
            threat_level=threat_level,
            expected_goal_value=xg_value,
            distance_to_goal=distance_to_goal,
            angle_to_goal=angle_to_goal,
            defenders_nearby=defenders_nearby,
            attackers_nearby=attackers_nearby,
            recommended_actions=recommendations
        )

        logger.debug(
            f"Assessed threat",
            threat_level=threat_level,
            threat_value=threat_value,
            distance=distance_to_goal
        )

        return assessment

    def calculate_defensive_action_value(
        self,
        action_id: str,
        match_id: str,
        player_id: str,
        team_id: str,
        action_type: DefensiveActionType,
        position: Position,
        threat_before: float,
        successful: bool,
        possession_regained: bool
    ) -> DefensiveAction:
        """
        Calculate the value of a defensive action (DAxT).

        Args:
            action_id: Action identifier
            match_id: Match identifier
            player_id: Defending player ID
            team_id: Defending team ID
            action_type: Type of defensive action
            position: Position where action occurred
            threat_before: Threat value before action
            successful: Whether action was successful
            possession_regained: Whether possession was regained

        Returns:
            DefensiveAction: Defensive action with calculated value
        """
        # Calculate threat after action
        if successful:
            if possession_regained:
                # Possession regained - threat significantly reduced
                threat_after = max(0.0, threat_before * 0.1)
            else:
                # Action successful but no possession - moderate reduction
                threat_after = max(0.0, threat_before * 0.5)
        else:
            # Action failed - threat may increase
            threat_after = min(1.0, threat_before * 1.2)

        # Calculate threat reduction (DAxT value)
        threat_reduction = threat_before - threat_after

        action = DefensiveAction(
            action_id=action_id,
            match_id=match_id,
            timestamp=datetime.utcnow(),
            player_id=player_id,
            team_id=team_id,
            action_type=action_type,
            position_x=position.x,
            position_y=position.y,
            threat_before=threat_before,
            threat_after=threat_after,
            threat_reduction=threat_reduction,
            successful=successful,
            possession_regained=possession_regained
        )

        logger.info(
            f"Calculated defensive action value",
            player_id=player_id,
            action_type=action_type,
            daxt_value=threat_reduction,
            successful=successful
        )

        return action

    def _calculate_distance(self, pos1: Position, pos2: Position) -> float:
        """Calculate Euclidean distance between two positions."""
        return math.sqrt((pos2.x - pos1.x) ** 2 + (pos2.y - pos1.y) ** 2)

    def _calculate_angle_to_goal(self, position: Position) -> float:
        """
        Calculate angle to goal from position.

        Args:
            position: Ball position

        Returns:
            float: Angle in degrees
        """
        goal_position = Position(x=120.0, y=40.0)

        # Calculate angle using arctangent
        dx = goal_position.x - position.x
        dy = goal_position.y - position.y

        angle_rad = math.atan2(abs(dy), dx)
        angle_deg = math.degrees(angle_rad)

        return angle_deg

    def _count_nearby_players(
        self,
        position: Position,
        players: List[PlayerTrackingEvent],
        radius: float
    ) -> int:
        """Count players within radius of position."""
        count = 0
        for player in players:
            if player.position:
                distance = self._calculate_distance(position, player.position)
                if distance <= radius:
                    count += 1
        return count

    def _calculate_threat_value(
        self,
        ball_position: Position,
        distance_to_goal: float,
        angle_to_goal: float,
        defenders_nearby: int,
        attackers_nearby: int
    ) -> float:
        """
        Calculate threat value using spatial model.

        Args:
            ball_position: Ball position
            distance_to_goal: Distance to goal
            angle_to_goal: Angle to goal
            defenders_nearby: Number of nearby defenders
            attackers_nearby: Number of nearby attackers

        Returns:
            float: Threat value (0-1)
        """
        # Base threat from distance (closer = higher threat)
        distance_threat = 1.0 / (1.0 + 0.05 * distance_to_goal)

        # Angle factor (straight on = higher threat)
        angle_factor = 1.0 - (angle_to_goal / 90.0)

        # Player advantage factor
        if defenders_nearby > 0:
            player_factor = attackers_nearby / (attackers_nearby + defenders_nearby)
        else:
            player_factor = 1.0

        # Position factor (in penalty box = higher threat)
        in_penalty_box = ball_position.x >= 102 and 22 <= ball_position.y <= 58
        position_factor = 1.5 if in_penalty_box else 1.0

        # Combine factors
        threat = distance_threat * angle_factor * player_factor * position_factor

        # Normalize to 0-1
        return min(max(threat, 0.0), 1.0)

    def _calculate_xg_from_position(
        self,
        position: Position,
        distance: float,
        angle: float
    ) -> float:
        """Calculate expected goal value from position."""
        # Simplified xG model
        xg = 1.0 / (1.0 + math.exp(0.1 * distance - 3 + 0.5 * angle / 90.0))
        return min(max(xg, 0.0), 1.0)

    def _categorize_threat(self, threat_value: float) -> ThreatLevel:
        """Categorize threat value into levels."""
        if threat_value > 0.8:
            return ThreatLevel.CRITICAL
        elif threat_value > 0.6:
            return ThreatLevel.HIGH
        elif threat_value > 0.4:
            return ThreatLevel.MEDIUM
        elif threat_value > 0.2:
            return ThreatLevel.LOW
        else:
            return ThreatLevel.MINIMAL

    def _generate_defensive_recommendations(
        self,
        threat_level: ThreatLevel,
        defenders_nearby: int,
        attackers_nearby: int,
        ball_position: Position
    ) -> List[str]:
        """Generate defensive recommendations based on threat."""
        recommendations = []

        if threat_level in [ThreatLevel.CRITICAL, ThreatLevel.HIGH]:
            if defenders_nearby < attackers_nearby:
                recommendations.append("Urgent: Send additional defenders")

            if ball_position.x > 100:
                recommendations.append("Priority: Prevent shot on goal")
                recommendations.append("Consider tactical foul if necessary")

            recommendations.append("Maintain compact defensive shape")
            recommendations.append("Close passing lanes to dangerous areas")

        elif threat_level == ThreatLevel.MEDIUM:
            recommendations.append("Apply moderate pressure")
            recommendations.append("Track attacking runs")
            recommendations.append("Maintain defensive organization")

        elif threat_level == ThreatLevel.LOW:
            recommendations.append("Maintain defensive position")
            recommendations.append("Look for counter-attack opportunities")

        return recommendations
