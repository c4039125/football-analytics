#!/usr/bin/env python3
"""
Generate synthetic football match data for testing.

This script creates realistic match scenarios with:
- Match events (goals, passes, tackles, etc.)
- Player tracking data (25 Hz)
- Physiological metrics

Usage:
    python generate_synthetic_data.py --matches 10 --output data/synthetic
"""

import argparse
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import sys
import math

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.event_models import (
    EventType,
    MatchEvent,
    PlayerTrackingEvent,
    PhysiologicalEvent,
    Position,
    Velocity,
)


class SyntheticDataGenerator:
    """Generate synthetic football match data."""

    def __init__(self, seed: int = 42):
        """
        Initialize generator.

        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.tracking_frequency_hz = 25  # 25 Hz tracking data
        self.match_duration_minutes = 90
        self.players_per_team = 11

    def generate_match_id(self) -> str:
        """Generate unique match ID."""
        return f"match_{uuid.uuid4().hex[:8]}"

    def generate_team_data(self, team_id: str, team_name: str) -> List[Dict[str, Any]]:
        """
        Generate team roster.

        Args:
            team_id: Team identifier
            team_name: Team name

        Returns:
            List of player data
        """
        players = []
        formations = {
            "GK": 1,
            "DEF": 4,
            "MID": 4,
            "FWD": 2
        }

        player_num = 1
        for position, count in formations.items():
            for i in range(count):
                players.append({
                    "player_id": f"{team_id}_p{player_num}",
                    "player_name": f"Player {player_num}",
                    "team_id": team_id,
                    "team_name": team_name,
                    "jersey_number": player_num,
                    "position": position
                })
                player_num += 1

        return players

    def generate_player_position(
        self,
        position_type: str,
        team_side: str,
        minute: int
    ) -> Position:
        """
        Generate realistic player position based on role and match time.

        Args:
            position_type: Player position (GK, DEF, MID, FWD)
            team_side: "home" or "away"
            minute: Current minute

        Returns:
            Position object
        """
        # Pitch dimensions: 120m x 80m
        # Home team attacks from 0 to 120, away team from 120 to 0

        base_x = 0 if team_side == "home" else 120
        direction = 1 if team_side == "home" else -1

        # Position ranges by role
        position_ranges = {
            "GK": (5, 15),
            "DEF": (15, 35),
            "MID": (35, 65),
            "FWD": (65, 95)
        }

        x_min, x_max = position_ranges.get(position_type, (40, 80))

        # Add some randomness and match flow
        x = base_x + direction * random.uniform(x_min, x_max)
        y = random.uniform(10, 70)  # Y position across pitch width

        # Clamp to pitch dimensions
        x = max(0, min(120, x))
        y = max(0, min(80, y))

        return Position(x=x, y=y)

    def generate_velocity(self) -> Velocity:
        """Generate realistic velocity."""
        # Max speed around 10 m/s (36 km/h)
        speed = random.uniform(0, 10)
        angle = random.uniform(0, 360)

        vx = speed * math.cos(math.radians(angle))
        vy = speed * math.sin(math.radians(angle))

        return Velocity(vx=vx, vy=vy, speed=speed)

    def generate_match_events(
        self,
        match_id: str,
        home_team: List[Dict],
        away_team: List[Dict]
    ) -> List[MatchEvent]:
        """
        Generate realistic match events.

        Args:
            match_id: Match identifier
            home_team: Home team players
            away_team: Away team players

        Returns:
            List of match events
        """
        events = []
        current_time = datetime.utcnow()

        # Generate events throughout the match
        num_events = random.randint(800, 1200)  # Typical match has ~1000 events

        for _ in range(num_events):
            minute = random.randint(0, 90)
            second = random.randint(0, 59)
            period = 1 if minute < 45 else 2

            # Choose event type (weighted probabilities)
            event_weights = {
                EventType.PASS: 0.6,
                EventType.TACKLE: 0.15,
                EventType.SHOT: 0.05,
                EventType.FOUL: 0.08,
                EventType.CORNER: 0.03,
                EventType.GOAL: 0.01,
                EventType.SUBSTITUTION: 0.02,
                EventType.CARD_YELLOW: 0.04,
                EventType.CARD_RED: 0.002,
            }

            event_type = random.choices(
                list(event_weights.keys()),
                weights=list(event_weights.values())
            )[0]

            # Choose team and player
            team = random.choice([home_team, away_team])
            player = random.choice(team)

            # Generate position
            position = self.generate_player_position(
                player["position"],
                "home" if team == home_team else "away",
                minute
            )

            # Generate end position for passes/shots
            end_position = None
            if event_type in [EventType.PASS, EventType.SHOT]:
                end_x = position.x + random.uniform(-30, 30)
                end_y = position.y + random.uniform(-20, 20)
                end_position = Position(
                    x=max(0, min(120, end_x)),
                    y=max(0, min(80, end_y))
                )

            outcome = "success" if random.random() > 0.3 else "fail"

            event = MatchEvent(
                event_id=str(uuid.uuid4()),
                match_id=match_id,
                timestamp=current_time + timedelta(minutes=minute, seconds=second),
                event_type=event_type,
                period=period,
                minute=minute,
                second=second,
                team_id=player["team_id"],
                team_name=player["team_name"],
                player_id=player["player_id"],
                player_name=player["player_name"],
                position=position,
                end_position=end_position,
                outcome=outcome,
                possession_team_id=player["team_id"]
            )

            events.append(event)

        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)

        return events

    def generate_tracking_data(
        self,
        match_id: str,
        home_team: List[Dict],
        away_team: List[Dict],
        duration_minutes: int = 90
    ) -> List[PlayerTrackingEvent]:
        """
        Generate player tracking data at 25 Hz.

        Args:
            match_id: Match identifier
            home_team: Home team players
            away_team: Away team players
            duration_minutes: Match duration

        Returns:
            List of tracking events
        """
        tracking_events = []
        current_time = datetime.utcnow()

        all_players = home_team + away_team
        total_frames = duration_minutes * 60 * self.tracking_frequency_hz

        # Sample frames (generate every 10th frame to reduce data volume)
        sample_rate = 10
        for frame in range(0, total_frames, sample_rate):
            minute = frame // (60 * self.tracking_frequency_hz)
            period = 1 if minute < 45 else 2

            for player in all_players:
                position = self.generate_player_position(
                    player["position"],
                    "home" if player in home_team else "away",
                    minute
                )

                velocity = self.generate_velocity()

                event = PlayerTrackingEvent(
                    event_id=str(uuid.uuid4()),
                    match_id=match_id,
                    timestamp=current_time + timedelta(
                        seconds=frame / self.tracking_frequency_hz
                    ),
                    event_type=EventType.PLAYER_POSITION,
                    player_id=player["player_id"],
                    team_id=player["team_id"],
                    jersey_number=player["jersey_number"],
                    position=position,
                    velocity=velocity,
                    period=period,
                    frame_id=frame,
                    in_possession=False  # Simplified
                )

                tracking_events.append(event)

        return tracking_events

    def generate_physiological_data(
        self,
        match_id: str,
        home_team: List[Dict],
        away_team: List[Dict],
        duration_minutes: int = 90
    ) -> List[PhysiologicalEvent]:
        """
        Generate physiological metrics data.

        Args:
            match_id: Match identifier
            home_team: Home team players
            away_team: Away team players
            duration_minutes: Match duration

        Returns:
            List of physiological events
        """
        physio_events = []
        current_time = datetime.utcnow()

        all_players = home_team + away_team

        # Generate data every 5 minutes for each player
        for minute in range(0, duration_minutes, 5):
            for player in all_players:
                # Simulate increasing fatigue over time
                fatigue_factor = minute / duration_minutes

                event = PhysiologicalEvent(
                    event_id=str(uuid.uuid4()),
                    match_id=match_id,
                    timestamp=current_time + timedelta(minutes=minute),
                    event_type=EventType.HEART_RATE,
                    player_id=player["player_id"],
                    team_id=player["team_id"],
                    heart_rate=int(random.uniform(150, 190) + fatigue_factor * 10),
                    distance_covered=minute * random.uniform(80, 120),
                    high_intensity_distance=minute * random.uniform(15, 25),
                    sprint_distance=minute * random.uniform(5, 15),
                    player_load=minute * random.uniform(5, 10),
                    fatigue_index=min(0.95, fatigue_factor + random.uniform(0, 0.2)),
                    max_speed=random.uniform(7, 10),
                    avg_speed=random.uniform(4, 6)
                )

                physio_events.append(event)

        return physio_events

    def generate_match(self, match_num: int = 1) -> Dict[str, Any]:
        """
        Generate complete match data.

        Args:
            match_num: Match number

        Returns:
            Dictionary with all match data
        """
        match_id = self.generate_match_id()

        home_team = self.generate_team_data(
            f"team_home_{match_num}",
            f"Home Team {match_num}"
        )
        away_team = self.generate_team_data(
            f"team_away_{match_num}",
            f"Away Team {match_num}"
        )

        print(f"Generating match {match_num} ({match_id})...")

        print("  - Generating match events...")
        match_events = self.generate_match_events(match_id, home_team, away_team)

        print("  - Generating tracking data...")
        tracking_events = self.generate_tracking_data(
            match_id, home_team, away_team, duration_minutes=10  # Reduced for testing
        )

        print("  - Generating physiological data...")
        physio_events = self.generate_physiological_data(
            match_id, home_team, away_team, duration_minutes=90
        )

        return {
            "match_id": match_id,
            "home_team": home_team,
            "away_team": away_team,
            "match_events": [e.model_dump(mode='json') for e in match_events],
            "tracking_events": [e.model_dump(mode='json') for e in tracking_events],
            "physiological_events": [e.model_dump(mode='json') for e in physio_events],
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_events": len(match_events) + len(tracking_events) + len(physio_events)
            }
        }


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic football match data"
    )
    parser.add_argument(
        "--matches",
        type=int,
        default=5,
        help="Number of matches to generate"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/synthetic",
        help="Output directory"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    generator = SyntheticDataGenerator(seed=args.seed)

    print(f"Generating {args.matches} synthetic matches...")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    for i in range(1, args.matches + 1):
        match_data = generator.generate_match(i)

        # Save match data
        match_file = output_dir / f"match_{match_data['match_id']}.json"
        with open(match_file, 'w') as f:
            json.dump(match_data, f, indent=2)

        print(f"  ✓ Saved to {match_file}")
        print(f"    Total events: {match_data['metadata']['total_events']:,}")

    print("=" * 60)
    print(f"✓ Successfully generated {args.matches} matches!")
    print(f"  Location: {output_dir}")


if __name__ == "__main__":
    main()
