"""Nigerian Football Data Integration (NPFL support)."""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from enum import Enum

from ..models.event_models import (
    MatchEvent,
    PlayerTrackingEvent,
    EventType,
    Position,
)
from ..utils.logger import get_logger
from ..utils.config import get_settings

logger = get_logger(__name__)


class NigerianLeague(str, Enum):
    """Nigerian football leagues."""

    NPFL = "npfl"
    NPL = "npl"
    NNL = "nnl"
    SUPER_CUP = "super_cup"


class NigerianFootballDataFetcher:
    """Nigerian football data fetcher (API-Football integration)."""

    def __init__(self):
        self.settings = get_settings()
        self.api_football_key = os.getenv('API_FOOTBALL_KEY')
        self.api_football_base = "https://v3.football.api-sports.io"
        self.league_ids = {
            NigerianLeague.NPFL: 403,
        }
        logger.info("Initialized Nigerian Football Data Fetcher")

    def get_available_leagues(self) -> List[Dict[str, Any]]:
        """Get available Nigerian leagues."""
        return [
            {
                "id": NigerianLeague.NPFL,
                "name": "Nigerian Professional Football League",
                "country": "Nigeria",
                "type": "League",
                "coverage": "API-Football"
            },
            {
                "id": NigerianLeague.NPL,
                "name": "Nigeria Premier League",
                "country": "Nigeria",
                "type": "League",
                "coverage": "Limited"
            },
            {
                "id": NigerianLeague.NNL,
                "name": "Nigeria National League",
                "country": "Nigeria",
                "type": "League",
                "coverage": "Limited"
            }
        ]

    def fetch_npfl_matches(
        self,
        season: int = 2024,
        team_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch NPFL matches from API-Football.

        Args:
            season: Season year
            team_id: Optional team filter

        Returns:
            list: Match data
        """
        if not self.api_football_key:
            logger.warning("API-Football key not configured")
            return []

        try:
            headers = {
                'x-rapidapi-host': 'v3.football.api-sports.io',
                'x-rapidapi-key': self.api_football_key
            }

            params = {
                'league': self.league_ids[NigerianLeague.NPFL],
                'season': season
            }

            if team_id:
                params['team'] = team_id

            response = requests.get(
                f"{self.api_football_base}/fixtures",
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                matches = data.get('response', [])
                logger.info(f"Fetched {len(matches)} NPFL matches")
                return matches
            else:
                logger.error(f"API-Football error: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch NPFL matches", error=str(e))
            return []

    def fetch_npfl_teams(self, season: int = 2024) -> List[Dict[str, Any]]:
        """
        Fetch NPFL teams.

        Args:
            season: Season year

        Returns:
            list: Team data
        """
        if not self.api_football_key:
            logger.warning("API-Football key not configured")
            return self._get_npfl_teams_fallback()

        try:
            headers = {
                'x-rapidapi-host': 'v3.football.api-sports.io',
                'x-rapidapi-key': self.api_football_key
            }

            params = {
                'league': self.league_ids[NigerianLeague.NPFL],
                'season': season
            }

            response = requests.get(
                f"{self.api_football_base}/teams",
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                teams = data.get('response', [])
                logger.info(f"Fetched {len(teams)} NPFL teams")
                return teams
            else:
                logger.error(f"API-Football error: {response.status_code}")
                return self._get_npfl_teams_fallback()

        except Exception as e:
            logger.error(f"Failed to fetch NPFL teams", error=str(e))
            return self._get_npfl_teams_fallback()

    def _get_npfl_teams_fallback(self) -> List[Dict[str, Any]]:
        """
        Get NPFL teams fallback data (2023/2024 season).

        Returns:
            list: Team data
        """
        # NPFL teams (2023/2024 season)
        return [
            {"id": 1, "name": "Enyimba FC", "city": "Aba", "founded": 1976},
            {"id": 2, "name": "Kano Pillars", "city": "Kano", "founded": 1990},
            {"id": 3, "name": "Rangers International", "city": "Enugu", "founded": 1970},
            {"id": 4, "name": "Plateau United", "city": "Jos", "founded": 1975},
            {"id": 5, "name": "Rivers United", "city": "Port Harcourt", "founded": 2016},
            {"id": 6, "name": "Remo Stars", "city": "Ikenne", "founded": 1965},
            {"id": 7, "name": "Shooting Stars", "city": "Ibadan", "founded": 1963},
            {"id": 8, "name": "Lobi Stars", "city": "Makurdi", "founded": 1983},
            {"id": 9, "name": "Akwa United", "city": "Uyo", "founded": 1996},
            {"id": 10, "name": "Bendel Insurance", "city": "Benin City", "founded": 1973},
            {"id": 11, "name": "Sunshine Stars", "city": "Akure", "founded": 1995},
            {"id": 12, "name": "Kwara United", "city": "Ilorin", "founded": 2007},
            {"id": 13, "name": "Heartland FC", "city": "Owerri", "founded": 1976},
            {"id": 14, "name": "Nasarawa United", "city": "Lafia", "founded": 2000},
            {"id": 15, "name": "Doma United", "city": "Doma", "founded": 2020},
            {"id": 16, "name": "Gombe United", "city": "Gombe", "founded": 2008},
            {"id": 17, "name": "Abia Warriors", "city": "Umuahia", "founded": 2005},
            {"id": 18, "name": "Sporting Lagos", "city": "Lagos", "founded": 2021},
            {"id": 19, "name": "Bayelsa United", "city": "Yenagoa", "founded": 2009},
            {"id": 20, "name": "Niger Tornadoes", "city": "Minna", "founded": 1975},
        ]

    def convert_to_match_events(
        self,
        api_match_data: Dict[str, Any]
    ) -> List[MatchEvent]:
        """
        Convert API match data to MatchEvent objects.

        Args:
            api_match_data: Match data from API

        Returns:
            list: MatchEvent objects
        """
        events = []

        try:
            fixture = api_match_data.get('fixture', {})
            teams = api_match_data.get('teams', {})
            goals = api_match_data.get('goals', {})

            match_id = f"npfl_{fixture.get('id', 'unknown')}"
            timestamp = datetime.fromisoformat(
                fixture.get('date', datetime.utcnow().isoformat()).replace('Z', '+00:00')
            )

            # Create goal events
            home_goals = goals.get('home', 0) or 0
            away_goals = goals.get('away', 0) or 0

            for i in range(home_goals):
                event = MatchEvent(
                    event_id=f"{match_id}_home_goal_{i}",
                    match_id=match_id,
                    timestamp=timestamp,
                    event_type=EventType.GOAL,
                    period=1,  # Simplified
                    minute=45 * i // max(home_goals, 1),
                    second=0,
                    team_id=str(teams.get('home', {}).get('id', 'unknown')),
                    team_name=teams.get('home', {}).get('name', 'Unknown'),
                    position=Position(x=110.0, y=40.0),  # Approximate
                    outcome="success"
                )
                events.append(event)

            for i in range(away_goals):
                event = MatchEvent(
                    event_id=f"{match_id}_away_goal_{i}",
                    match_id=match_id,
                    timestamp=timestamp,
                    event_type=EventType.GOAL,
                    period=1,  # Simplified
                    minute=45 * i // max(away_goals, 1),
                    second=0,
                    team_id=str(teams.get('away', {}).get('id', 'unknown')),
                    team_name=teams.get('away', {}).get('name', 'Unknown'),
                    position=Position(x=110.0, y=40.0),  # Approximate
                    outcome="success"
                )
                events.append(event)

            logger.info(f"Converted API data to {len(events)} events")
            return events

        except Exception as e:
            logger.error(f"Failed to convert match data", error=str(e))
            return []


def get_nigerian_football_data_configuration() -> Dict[str, Any]:
    """
    Get configuration for Nigerian football data sources.

    Returns:
        dict: Configuration
    """
    return {
        "primary_league": "NPFL",
        "api_sources": [
            {
                "name": "API-Football",
                "url": "https://api-football.com",
                "supports_npfl": True,
                "requires_key": True,
                "coverage": "matches, teams, standings, statistics"
            },
            {
                "name": "Football-Data.org",
                "url": "https://www.football-data.org",
                "supports_npfl": False,
                "requires_key": True,
                "coverage": "limited"
            }
        ],
        "recommended_api": "API-Football",
        "setup_instructions": {
            "step1": "Sign up at api-football.com",
            "step2": "Get API key from dashboard",
            "step3": "Set API_FOOTBALL_KEY environment variable",
            "step4": "Configure in config/config.env"
        },
        "npfl_league_id": 403,
        "season": 2024
    }
