"""Analytics engine for computing football metrics."""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.event_models import MatchEvent, PlayerTrackingEvent, Position
from ..models.analytics_models import (
    PlayerPerformanceMetrics,
    MatchStatistics,
    PlayerRole,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsEngine:
    """Analytics engine for football metrics."""

    def __init__(self):
        logger.info("Analytics engine initialized")

    def calculate_player_performance(
        self,
        player_id: str,
        player_name: str,
        team_id: str,
        match_id: str,
        events: List[MatchEvent],
        role: PlayerRole = PlayerRole.MIDFIELDER
    ) -> PlayerPerformanceMetrics:
        """Calculate player performance metrics."""
        metrics = PlayerPerformanceMetrics(
            player_id=player_id,
            player_name=player_name,
            team_id=team_id,
            match_id=match_id,
            timestamp=datetime.utcnow(),
            role=role
        )

        for event in events:
            event_type = event.event_type.value if hasattr(event.event_type, 'value') else event.event_type

            if event_type == 'goal':
                metrics.goals += 1
            elif event_type == 'shot':
                metrics.shots += 1
                if event.outcome == 'success' or event.metadata.get('on_target'):
                    metrics.shots_on_target += 1
            elif event_type == 'pass':
                metrics.passes_attempted += 1
                if event.outcome == 'success':
                    metrics.passes_completed += 1
                if event.metadata.get('key_pass'):
                    metrics.key_passes += 1
                if self._is_progressive_pass(event):
                    metrics.progressive_passes += 1
            elif event_type == 'tackle':
                metrics.tackles_attempted += 1
                if event.outcome == 'success':
                    metrics.tackles_won += 1
            elif event_type == 'interception':
                metrics.interceptions += 1
            elif event_type == 'clearance':
                metrics.clearances += 1
            elif event_type == 'block':
                metrics.blocks += 1
        if metrics.passes_attempted > 0:
            metrics.pass_accuracy = metrics.passes_completed / metrics.passes_attempted

        # Calculate expected goals (simplified)
        metrics.expected_goals = self._calculate_expected_goals(events)

        # Calculate performance score (0-10)
        metrics.performance_score = self._calculate_performance_score(metrics, role)

        logger.info(
            f"Calculated player performance",
            player_id=player_id,
            goals=metrics.goals,
            passes=metrics.passes_completed,
            score=metrics.performance_score
        )

        return metrics

    def calculate_match_statistics(
        self,
        match_id: str,
        home_team_id: str,
        away_team_id: str,
        events: List[MatchEvent]
    ) -> MatchStatistics:
        """
        Calculate aggregated match statistics.

        Args:
            match_id: Match identifier
            home_team_id: Home team ID
            away_team_id: Away team ID
            events: All match events

        Returns:
            MatchStatistics: Calculated statistics
        """
        stats = MatchStatistics(
            match_id=match_id,
            timestamp=datetime.utcnow(),
            home_team_id=home_team_id,
            away_team_id=away_team_id
        )

        home_events = [e for e in events if e.team_id == home_team_id]
        away_events = [e for e in events if e.team_id == away_team_id]

        # Count goals
        stats.home_score = sum(1 for e in home_events if e.event_type.value == 'goal')
        stats.away_score = sum(1 for e in away_events if e.event_type.value == 'goal')

        # Count shots
        stats.home_shots = sum(1 for e in home_events if e.event_type.value == 'shot')
        stats.away_shots = sum(1 for e in away_events if e.event_type.value == 'shot')

        stats.home_shots_on_target = sum(
            1 for e in home_events
            if e.event_type.value == 'shot' and (e.outcome == 'success' or e.metadata.get('on_target'))
        )
        stats.away_shots_on_target = sum(
            1 for e in away_events
            if e.event_type.value == 'shot' and (e.outcome == 'success' or e.metadata.get('on_target'))
        )

        # Count passes
        home_passes = [e for e in home_events if e.event_type.value == 'pass']
        away_passes = [e for e in away_events if e.event_type.value == 'pass']

        stats.home_passes = len(home_passes)
        stats.away_passes = len(away_passes)

        home_pass_success = sum(1 for e in home_passes if e.outcome == 'success')
        away_pass_success = sum(1 for e in away_passes if e.outcome == 'success')

        if stats.home_passes > 0:
            stats.home_pass_accuracy = home_pass_success / stats.home_passes
        if stats.away_passes > 0:
            stats.away_pass_accuracy = away_pass_success / stats.away_passes

        # Calculate possession (simplified - based on pass count)
        total_passes = stats.home_passes + stats.away_passes
        if total_passes > 0:
            stats.home_possession = stats.home_passes / total_passes
            stats.away_possession = stats.away_passes / total_passes

        # Calculate expected goals
        stats.home_xg = sum(self._calculate_shot_xg(e) for e in home_events if e.event_type.value == 'shot')
        stats.away_xg = sum(self._calculate_shot_xg(e) for e in away_events if e.event_type.value == 'shot')

        logger.info(
            f"Calculated match statistics",
            match_id=match_id,
            score=f"{stats.home_score}-{stats.away_score}",
            possession=f"{stats.home_possession:.1%}-{stats.away_possession:.1%}"
        )

        return stats

    def _is_progressive_pass(self, event: MatchEvent) -> bool:
        """
        Check if a pass is progressive (moves ball significantly forward).

        Args:
            event: Pass event

        Returns:
            bool: True if progressive
        """
        if not event.position or not event.end_position:
            return False

        # Progressive if moves ball at least 10m forward
        forward_distance = event.end_position.x - event.position.x
        return forward_distance >= 10

    def _calculate_expected_goals(self, events: List[MatchEvent]) -> float:
        """
        Calculate expected goals for a player from their shots.

        Args:
            events: Player events

        Returns:
            float: Expected goals value
        """
        xg_total = 0.0
        for event in events:
            if event.event_type.value == 'shot':
                xg_total += self._calculate_shot_xg(event)
        return xg_total

    def _calculate_shot_xg(self, event: MatchEvent) -> float:
        """
        Calculate expected goal value for a single shot.

        Args:
            event: Shot event

        Returns:
            float: xG value (0-1)
        """
        if not event.position:
            return 0.1  # Default low value

        # Goal position (center of goal at x=120, y=40)
        goal_x, goal_y = 120, 40

        # Calculate distance to goal
        distance = math.sqrt(
            (goal_x - event.position.x) ** 2 +
            (goal_y - event.position.y) ** 2
        )

        # Calculate angle to goal
        angle = abs(math.atan2(goal_y - event.position.y, goal_x - event.position.x))

        # Simplified xG model (logistic regression approximation)
        # Real models use machine learning with more features
        xg = 1 / (1 + math.exp(0.1 * distance - 3 + 0.5 * angle))

        # Bonus for shots on target
        if event.outcome == 'success' or event.metadata.get('on_target'):
            xg *= 1.2

        return min(max(xg, 0.01), 0.99)

    def _calculate_performance_score(
        self,
        metrics: PlayerPerformanceMetrics,
        role: PlayerRole
    ) -> float:
        """
        Calculate overall performance score (0-10) based on role.

        Args:
            metrics: Player metrics
            role: Player role

        Returns:
            float: Performance score
        """
        score = 5.0  # Base score

        # Role-specific scoring
        if role == PlayerRole.GOALKEEPER:
            # Goalkeepers scored on saves, not goals
            score += min(2.0, metrics.blocks * 0.5)

        elif role in [PlayerRole.DEFENDER, PlayerRole.DEFENSIVE_MIDFIELDER]:
            # Defensive players
            score += min(2.0, metrics.tackles_won * 0.2)
            score += min(1.5, metrics.interceptions * 0.15)
            score += min(1.0, metrics.clearances * 0.1)
            score -= metrics.goals * 0.5  # Penalty for conceding

        elif role in [PlayerRole.MIDFIELDER, PlayerRole.ATTACKING_MIDFIELDER]:
            # Midfielders
            score += min(2.0, metrics.passes_completed * 0.01)
            score += min(1.5, metrics.key_passes * 0.3)
            score += min(1.0, metrics.goals * 0.5)
            score += min(0.5, metrics.assists * 0.4)

        elif role in [PlayerRole.FORWARD, PlayerRole.STRIKER, PlayerRole.WINGER]:
            # Attacking players
            score += min(3.0, metrics.goals * 1.0)
            score += min(2.0, metrics.assists * 0.8)
            score += min(1.0, metrics.shots_on_target * 0.2)
            score += min(0.5, metrics.expected_goals * 0.5)

        # General bonuses
        if metrics.pass_accuracy > 0.85:
            score += 0.5

        # Ensure score is between 0-10
        return min(max(score, 0.0), 10.0)
