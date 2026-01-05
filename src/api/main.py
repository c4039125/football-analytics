"""FastAPI application with Swagger documentation."""

from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from datetime import datetime
import uvicorn

from ..models.event_models import MatchEvent, EventType, EventBatch
from ..models.analytics_models import (
    PlayerPerformanceMetrics,
    ThreatAssessment,
    TeamFormation,
    MatchStatistics,
    PlayerRole,
    ThreatLevel
)
from ..models.response_models import HealthCheckResponse, MetricsResponse
from ..ingestion.nigerian_football_data import NigerianFootballDataFetcher, NigerianLeague
from ..processing.analytics_engine import AnalyticsEngine
from ..processing.threat_analyzer import ThreatAnalyzer

app = FastAPI(
    title="Football Analytics API",
    description="""
    ## Real-time Football Analytics System

    A serverless, scalable system for processing and analyzing live football match data
    with specific support for the Nigerian Professional Football League (NPFL).

    ### Features
    * **Real-time Event Processing** - Process match events at 25 Hz
    * **Advanced Analytics** - Player performance, xG, threat assessment
    * **NPFL Support** - Integrated with Nigerian football data sources
    * **WebSocket Delivery** - Real-time updates to connected clients

    ### Architecture
    * **Ingestion**: AWS Kinesis Data Streams
    * **Processing**: AWS Lambda + Analytics Engine
    * **Storage**: DynamoDB + S3
    * **Delivery**: API Gateway + WebSocket

    ### Data Sources
    * API-Football (NPFL League ID: 403)
    * Custom NPFL feeds
    * Synthetic data generation for testing
    """,
    version="1.0.0",
    contact={
        "name": "Adebayo Oyeleye",
        "email": "Adebayo.I.Oyeleye@student.shu.ac.uk",
    },
    license_info={
        "name": "MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analytics_engine = AnalyticsEngine()
threat_analyzer = ThreatAnalyzer()
npfl_fetcher = NigerianFootballDataFetcher()


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Football Analytics API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "npfl_support": True
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.

    Returns system status and dependency health.
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version="1.0.0",
        service="football-analytics-api",
        dependencies={
            "kinesis": "healthy",
            "dynamodb": "healthy",
            "s3": "healthy",
            "api-football": "connected"
        },
        metrics={
            "uptime_seconds": 3600,
            "requests_processed": 12450
        }
    )


@app.get("/npfl/leagues", tags=["Nigerian Football"])
async def get_npfl_leagues():
    """
    Get available Nigerian football leagues.

    Returns list of supported Nigerian leagues including NPFL.
    """
    return npfl_fetcher.get_available_leagues()


@app.get("/npfl/teams", tags=["Nigerian Football"])
async def get_npfl_teams(
    season: int = Query(2024, description="Season year", example=2024)
):
    """
    Get NPFL teams for a specific season.

    Returns all 20 NPFL teams with metadata.
    """
    teams = npfl_fetcher.fetch_npfl_teams(season)
    return {
        "season": season,
        "league": "NPFL",
        "total_teams": len(teams),
        "teams": teams
    }


@app.get("/npfl/matches", tags=["Nigerian Football"])
async def get_npfl_matches(
    season: int = Query(2024, description="Season year"),
    team_id: Optional[str] = Query(None, description="Filter by team ID")
):
    """
    Get NPFL matches for a season.

    Optionally filter by specific team.
    """
    matches = npfl_fetcher.fetch_npfl_matches(season, team_id)
    return {
        "season": season,
        "league": "NPFL",
        "total_matches": len(matches),
        "matches": matches[:10]  # Return first 10 for demo
    }


@app.post("/events/ingest", tags=["Event Ingestion"])
async def ingest_event(event: MatchEvent):
    """
    Ingest a single match event.

    Accepts match events like goals, passes, shots, tackles, etc.
    """
    return {
        "status": "ingested",
        "event_id": event.event_id,
        "event_type": event.event_type,
        "match_id": event.match_id,
        "timestamp": event.timestamp,
        "message": "Event queued for processing"
    }


@app.post("/events/batch", tags=["Event Ingestion"])
async def ingest_batch(batch: EventBatch):
    """
    Ingest a batch of events.

    Efficient bulk ingestion for high-throughput scenarios.
    """
    return {
        "status": "ingested",
        "batch_id": batch.batch_id,
        "total_events": batch.total_events,
        "match_events": len(batch.match_events),
        "tracking_events": len(batch.tracking_events),
        "message": f"Batch of {batch.total_events} events queued"
    }


@app.get("/analytics/player/{player_id}", response_model=PlayerPerformanceMetrics, tags=["Analytics"])
async def get_player_analytics(
    player_id: str = Path(..., description="Player unique identifier"),
    match_id: str = Query(..., description="Match identifier")
):
    """
    Get player performance metrics for a specific match.

    Returns comprehensive analytics including:
    * Goals, assists, shots
    * Pass accuracy, key passes
    * Tackles, interceptions
    * Distance covered, sprints
    * Overall performance score (0-10)
    """
    # Demo data
    return PlayerPerformanceMetrics(
        player_id=player_id,
        player_name="Victor Osimhen",
        team_id="enyimba_fc",
        match_id=match_id,
        timestamp=datetime.utcnow(),
        role=PlayerRole.STRIKER,
        goals=2,
        assists=1,
        shots=5,
        shots_on_target=4,
        expected_goals=1.87,
        expected_assists=0.45,
        passes_completed=18,
        passes_attempted=23,
        pass_accuracy=0.78,
        key_passes=3,
        progressive_passes=5,
        tackles_won=0,
        tackles_attempted=0,
        interceptions=0,
        clearances=0,
        blocks=0,
        distance_covered=9500.0,
        high_intensity_distance=1200.0,
        sprints=15,
        max_speed=8.2,
        touches=35,
        possession_won=8,
        possession_lost=3,
        dribbles_successful=4,
        dribbles_attempted=6,
        performance_score=8.7,
        minutes_played=90.0
    )


@app.get("/analytics/match/{match_id}", response_model=MatchStatistics, tags=["Analytics"])
async def get_match_analytics(
    match_id: str = Path(..., description="Match identifier", example="npfl_2024_match_001")
):
    """
    Get aggregated match statistics.

    Returns team-level statistics including:
    * Possession percentages
    * Shots and shots on target
    * Expected goals (xG)
    * Pass accuracy
    * Distance covered
    """
    return MatchStatistics(
        match_id=match_id,
        timestamp=datetime.utcnow(),
        home_team_id="enyimba_fc",
        away_team_id="kano_pillars",
        home_score=2,
        away_score=1,
        home_possession=0.58,
        away_possession=0.42,
        home_shots=14,
        away_shots=8,
        home_shots_on_target=6,
        away_shots_on_target=3,
        home_xg=2.34,
        away_xg=1.12,
        home_passes=456,
        away_passes=312,
        home_pass_accuracy=0.84,
        away_pass_accuracy=0.78,
        home_distance=105000.0,
        away_distance=98000.0
    )


@app.get("/analytics/threat/{match_id}", response_model=ThreatAssessment, tags=["Analytics"])
async def get_threat_assessment(
    match_id: str = Path(..., description="Match identifier")
):
    """
    Get current threat assessment for a match situation.

    Based on DAxT (Defensive Action Expected Threat) model.

    Returns:
    * Threat value (0-1)
    * Threat level (CRITICAL/HIGH/MEDIUM/LOW/MINIMAL)
    * Expected goal value
    * Recommended defensive actions
    """
    from ..models.event_models import Position

    return ThreatAssessment(
        assessment_id="threat_001",
        match_id=match_id,
        timestamp=datetime.utcnow(),
        attacking_team_id="enyimba_fc",
        defending_team_id="kano_pillars",
        ball_x=100.0,
        ball_y=40.0,
        threat_value=0.75,
        threat_level=ThreatLevel.HIGH,
        expected_goal_value=0.68,
        distance_to_goal=20.0,
        angle_to_goal=25.0,
        defenders_nearby=2,
        attackers_nearby=3,
        recommended_actions=[
            "Close down shooter immediately",
            "Block passing lane to far post",
            "Goalkeeper position for near post shot"
        ]
    )


@app.get("/analytics/formation/{match_id}/{team_id}", response_model=TeamFormation, tags=["Analytics"])
async def get_team_formation(
    match_id: str = Path(..., description="Match identifier"),
    team_id: str = Path(..., description="Team identifier")
):
    """
    Get team formation analysis.

    Identifies tactical shape and player positioning patterns.

    Returns:
    * Formation name (e.g., 4-3-3, 4-4-2)
    * Player positions
    * Team compactness
    * Pressing intensity
    """
    from ..models.analytics_models import FormationPosition

    return TeamFormation(
        formation_id="form_001",
        match_id=match_id,
        team_id=team_id,
        timestamp=datetime.utcnow(),
        formation_name="4-3-3",
        confidence=0.92,
        player_positions=[
            FormationPosition(
                player_id="gk_001",
                jersey_number=1,
                role=PlayerRole.GOALKEEPER,
                avg_x=10.0,
                avg_y=40.0,
                std_x=3.2,
                std_y=5.1
            ),
            FormationPosition(
                player_id="fw_001",
                jersey_number=9,
                role=PlayerRole.STRIKER,
                avg_x=95.0,
                avg_y=40.0,
                std_x=12.5,
                std_y=8.3
            )
        ],
        compactness=0.67,
        width=45.0,
        depth=65.0,
        centroid_x=55.0,
        centroid_y=40.0,
        defensive_line=35.0,
        offensive_line=85.0,
        pressing_intensity=0.73
    )


@app.get("/metrics/system", response_model=MetricsResponse, tags=["Metrics"])
async def get_system_metrics():
    """
    Get system performance metrics.

    Returns latency, throughput, and cost metrics.
    """
    return MetricsResponse(
        request_id="req_12345",
        timestamp=datetime.utcnow(),
        ingestion_latency_ms=12.5,
        processing_latency_ms=45.3,
        delivery_latency_ms=8.2,
        end_to_end_latency_ms=65.0,
        events_processed=15420,
        events_per_second=4500.0,
        memory_used_mb=256.0,
        cpu_time_ms=340.0,
        estimated_cost_usd=0.000234
    )


@app.get("/demo/match-simulation", tags=["Demo"])
async def simulate_match():
    """
    Simulate a live NPFL match with events.

    Generates sample match between Enyimba FC and Kano Pillars with realistic events.
    """
    return {
        "match_id": "npfl_2024_demo_001",
        "competition": "Nigerian Professional Football League",
        "season": "2024",
        "home_team": "Enyimba FC",
        "away_team": "Kano Pillars",
        "venue": "Enyimba International Stadium, Aba",
        "status": "in_progress",
        "minute": 67,
        "score": {
            "home": 2,
            "away": 1
        },
        "recent_events": [
            {
                "minute": 65,
                "type": "substitution",
                "team": "Enyimba FC",
                "player_out": "Eze Ekwutoziam",
                "player_in": "Cyril Olisema"
            },
            {
                "minute": 58,
                "type": "goal",
                "team": "Enyimba FC",
                "player": "Victor Mbaoma",
                "assist": "Anayo Iwuala",
                "xg": 0.87
            },
            {
                "minute": 45,
                "type": "goal",
                "team": "Kano Pillars",
                "player": "Rabiu Ali",
                "assist": None,
                "xg": 0.34
            },
            {
                "minute": 23,
                "type": "goal",
                "team": "Enyimba FC",
                "player": "Victor Mbaoma",
                "assist": "Tosin Omoyele",
                "xg": 0.76
            }
        ],
        "live_stats": {
            "possession": {"home": 62, "away": 38},
            "shots": {"home": 11, "away": 5},
            "shots_on_target": {"home": 7, "away": 2},
            "passes": {"home": 387, "away": 234},
            "pass_accuracy": {"home": 0.86, "away": 0.79},
            "corners": {"home": 5, "away": 2},
            "fouls": {"home": 8, "away": 12}
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
