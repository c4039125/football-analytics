"""
Unit tests for event models.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.event_models import (
    EventType,
    MatchEvent,
    PlayerTrackingEvent,
    PhysiologicalEvent,
    Position,
    Velocity,
    EventBatch,
)


class TestPosition:
    """Test Position model."""

    def test_valid_position(self):
        """Test creating a valid position."""
        position = Position(x=60.0, y=40.0)
        assert position.x == 60.0
        assert position.y == 40.0

    def test_position_boundaries(self):
        """Test position boundary validation."""
        # Valid boundaries
        Position(x=0.0, y=0.0)
        Position(x=120.0, y=80.0)

        # Invalid x
        with pytest.raises(ValidationError):
            Position(x=-1.0, y=40.0)

        with pytest.raises(ValidationError):
            Position(x=121.0, y=40.0)

        # Invalid y
        with pytest.raises(ValidationError):
            Position(x=60.0, y=-1.0)

        with pytest.raises(ValidationError):
            Position(x=60.0, y=81.0)


class TestVelocity:
    """Test Velocity model."""

    def test_valid_velocity(self):
        """Test creating a valid velocity."""
        velocity = Velocity(vx=5.0, vy=3.0, speed=5.83)
        assert velocity.vx == 5.0
        assert velocity.vy == 3.0
        assert velocity.speed == 5.83

    def test_speed_non_negative(self):
        """Test that speed cannot be negative."""
        Velocity(vx=0.0, vy=0.0, speed=0.0)

        with pytest.raises(ValidationError):
            Velocity(vx=5.0, vy=3.0, speed=-1.0)


class TestMatchEvent:
    """Test MatchEvent model."""

    def test_valid_match_event(self):
        """Test creating a valid match event."""
        event = MatchEvent(
            event_id="evt_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.PASS,
            period=1,
            minute=15,
            second=30,
            team_id="team_001",
            team_name="Home Team",
            player_id="player_001",
            player_name="Player One",
            position=Position(x=60.0, y=40.0),
            outcome="success"
        )

        assert event.event_type == EventType.PASS
        assert event.period == 1
        assert event.minute == 15
        assert event.outcome == "success"

    def test_event_type_enum(self):
        """Test event type enumeration."""
        event = MatchEvent(
            event_id="evt_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.GOAL,
            period=2,
            minute=75,
            second=22,
            team_id="team_001",
            team_name="Home Team"
        )

        assert event.event_type == EventType.GOAL

    def test_period_validation(self):
        """Test period validation (1-5)."""
        # Valid periods
        for period in range(1, 6):
            MatchEvent(
                event_id=f"evt_{period}",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.PASS,
                period=period,
                minute=10,
                second=0,
                team_id="team_001",
                team_name="Team"
            )

        # Invalid period
        with pytest.raises(ValidationError):
            MatchEvent(
                event_id="evt_invalid",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.PASS,
                period=6,  # Invalid
                minute=10,
                second=0,
                team_id="team_001",
                team_name="Team"
            )


class TestPlayerTrackingEvent:
    """Test PlayerTrackingEvent model."""

    def test_valid_tracking_event(self):
        """Test creating a valid tracking event."""
        event = PlayerTrackingEvent(
            event_id="trk_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.PLAYER_POSITION,
            player_id="player_001",
            team_id="team_001",
            jersey_number=10,
            position=Position(x=60.0, y=40.0),
            velocity=Velocity(vx=5.0, vy=2.0, speed=5.39),
            period=1,
            frame_id=1000,
            in_possession=True
        )

        assert event.player_id == "player_001"
        assert event.jersey_number == 10
        assert event.in_possession is True

    def test_jersey_number_validation(self):
        """Test jersey number validation (1-99)."""
        # Valid jersey numbers
        for num in [1, 10, 50, 99]:
            PlayerTrackingEvent(
                event_id=f"trk_{num}",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.PLAYER_POSITION,
                player_id="player_001",
                team_id="team_001",
                jersey_number=num,
                position=Position(x=60.0, y=40.0),
                period=1,
                frame_id=1000
            )

        # Invalid jersey numbers
        with pytest.raises(ValidationError):
            PlayerTrackingEvent(
                event_id="trk_invalid",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.PLAYER_POSITION,
                player_id="player_001",
                team_id="team_001",
                jersey_number=0,  # Too low
                position=Position(x=60.0, y=40.0),
                period=1,
                frame_id=1000
            )


class TestPhysiologicalEvent:
    """Test PhysiologicalEvent model."""

    def test_valid_physiological_event(self):
        """Test creating a valid physiological event."""
        event = PhysiologicalEvent(
            event_id="physio_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.HEART_RATE,
            player_id="player_001",
            team_id="team_001",
            heart_rate=165,
            distance_covered=5420.5,
            high_intensity_distance=850.2,
            sprint_distance=125.0,
            player_load=245.8,
            fatigue_index=0.65,
            max_speed=9.2,
            avg_speed=5.1
        )

        assert event.heart_rate == 165
        assert event.distance_covered == 5420.5
        assert 0 <= event.fatigue_index <= 1

    def test_heart_rate_validation(self):
        """Test heart rate validation (40-220 bpm)."""
        # Valid heart rates
        PhysiologicalEvent(
            event_id="physio_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.HEART_RATE,
            player_id="player_001",
            team_id="team_001",
            heart_rate=170
        )

        # Invalid heart rate (too low)
        with pytest.raises(ValidationError):
            PhysiologicalEvent(
                event_id="physio_002",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.HEART_RATE,
                player_id="player_001",
                team_id="team_001",
                heart_rate=30
            )

    def test_fatigue_index_range(self):
        """Test fatigue index is between 0 and 1."""
        # Valid fatigue indices
        for fatigue in [0.0, 0.5, 1.0]:
            PhysiologicalEvent(
                event_id=f"physio_{fatigue}",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.HEART_RATE,
                player_id="player_001",
                team_id="team_001",
                fatigue_index=fatigue
            )

        # Invalid fatigue index
        with pytest.raises(ValidationError):
            PhysiologicalEvent(
                event_id="physio_invalid",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.HEART_RATE,
                player_id="player_001",
                team_id="team_001",
                fatigue_index=1.5  # Too high
            )


class TestEventBatch:
    """Test EventBatch model."""

    def test_valid_event_batch(self):
        """Test creating a valid event batch."""
        match_event = MatchEvent(
            event_id="evt_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.PASS,
            period=1,
            minute=10,
            second=0,
            team_id="team_001",
            team_name="Team"
        )

        tracking_event = PlayerTrackingEvent(
            event_id="trk_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.PLAYER_POSITION,
            player_id="player_001",
            team_id="team_001",
            jersey_number=10,
            position=Position(x=60.0, y=40.0),
            period=1,
            frame_id=1000
        )

        batch = EventBatch(
            batch_id="batch_001",
            match_id="match_001",
            ingestion_time=datetime.utcnow(),
            match_events=[match_event],
            tracking_events=[tracking_event],
            total_events=2
        )

        assert len(batch.match_events) == 1
        assert len(batch.tracking_events) == 1
        assert batch.total_events == 2

    def test_batch_total_events_calculation(self):
        """Test automatic calculation of total events."""
        match_events = [
            MatchEvent(
                event_id=f"evt_{i}",
                match_id="match_001",
                timestamp=datetime.utcnow(),
                event_type=EventType.PASS,
                period=1,
                minute=i,
                second=0,
                team_id="team_001",
                team_name="Team"
            ) for i in range(5)
        ]

        batch = EventBatch(
            batch_id="batch_001",
            match_id="match_001",
            ingestion_time=datetime.utcnow(),
            match_events=match_events,
            total_events=5
        )

        # The validator should set total_events to the actual count
        assert batch.total_events == 5


class TestEventSerialization:
    """Test event serialization."""

    def test_match_event_serialization(self):
        """Test match event can be serialized to dict."""
        event = MatchEvent(
            event_id="evt_001",
            match_id="match_001",
            timestamp=datetime.utcnow(),
            event_type=EventType.PASS,
            period=1,
            minute=10,
            second=0,
            team_id="team_001",
            team_name="Team"
        )

        # Test model_dump (Pydantic v2)
        event_dict = event.model_dump()
        assert isinstance(event_dict, dict)
        assert event_dict['event_id'] == 'evt_001'
        assert event_dict['event_type'] == EventType.PASS

        # Test JSON serialization
        event_json = event.model_dump_json()
        assert isinstance(event_json, str)
        assert 'evt_001' in event_json


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
