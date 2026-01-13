#!/usr/bin/env python3
"""
Live Football Data Ingestion Script
Fetches real NPFL match data from API-Football and sends to Kinesis
"""

import os
import sys
import json
import base64
import time
from datetime import datetime
from typing import List, Dict, Any
import requests
import boto3
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.env'))

API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
KINESIS_STREAM_NAME = f"football-analytics-stream-{os.getenv('ENVIRONMENT', 'development')}"

API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
NPFL_LEAGUE_ID = 399  # Nigeria Professional Football League

# Initialize AWS clients
kinesis = boto3.client('kinesis', region_name=AWS_REGION)


class NPFLDataIngestion:
    """Handles fetching and ingesting NPFL match data"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }

    def fetch_live_fixtures(self) -> List[Dict[str, Any]]:
        """Fetch live NPFL fixtures"""
        url = f"{API_FOOTBALL_BASE_URL}/fixtures"
        params = {
            'league': NPFL_LEAGUE_ID,
            'live': 'all',
            'season': 2024
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('response'):
                print(f"✅ Found {len(data['response'])} live NPFL matches")
                return data['response']
            else:
                print("ℹ️  No live NPFL matches currently")
                return []
        except Exception as e:
            print(f"❌ Error fetching live fixtures: {e}")
            return []

    def fetch_upcoming_fixtures(self, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch upcoming NPFL fixtures"""
        url = f"{API_FOOTBALL_BASE_URL}/fixtures"
        params = {
            'league': NPFL_LEAGUE_ID,
            'next': days,
            'season': 2024
        }

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('response'):
                print(f"✅ Found {len(data['response'])} upcoming NPFL matches")
                return data['response']
            else:
                print("ℹ️  No upcoming NPFL matches")
                return []
        except Exception as e:
            print(f"❌ Error fetching upcoming fixtures: {e}")
            return []

    def fetch_fixture_events(self, fixture_id: int) -> List[Dict[str, Any]]:
        """Fetch events for a specific match (goals, cards, substitutions)"""
        url = f"{API_FOOTBALL_BASE_URL}/fixtures/events"
        params = {'fixture': fixture_id}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            return data.get('response', [])
        except Exception as e:
            print(f"❌ Error fetching fixture events: {e}")
            return []

    def transform_event_to_kinesis_format(self, event: Dict[str, Any], fixture: Dict[str, Any]) -> Dict[str, Any]:
        """Transform API-Football event to our Kinesis event format"""

        # Map API-Football event types to our format
        event_type_mapping = {
            'Goal': 'goal',
            'Card': 'foul',
            'subst': 'substitution',
            'Var': 'var_check'
        }

        event_type = event_type_mapping.get(event.get('type'), 'other')

        # Extract team and player info
        team_name = event.get('team', {}).get('name', 'unknown')
        team_id = team_name.lower().replace(' ', '_')
        player_name = event.get('player', {}).get('name', 'unknown')
        player_id = player_name.lower().replace(' ', '_')

        # Create match ID
        match_id = f"npfl_2024_{fixture['fixture']['id']}"

        # Build the event
        kinesis_event = {
            'event_type': event_type,
            'match_id': match_id,
            'timestamp': datetime.utcnow().isoformat(),
            'team_id': team_id,
            'player_id': player_id,
            'metadata': {
                'minute': event.get('time', {}).get('elapsed', 0),
                'extra_time': event.get('time', {}).get('extra'),
                'detail': event.get('detail'),
                'comments': event.get('comments'),
                'home_team': fixture.get('teams', {}).get('home', {}).get('name'),
                'away_team': fixture.get('teams', {}).get('away', {}).get('name'),
                'score': f"{fixture.get('goals', {}).get('home')}-{fixture.get('goals', {}).get('away')}"
            }
        }

        # Add event-specific metadata
        if event_type == 'goal':
            kinesis_event['metadata']['goal_type'] = event.get('detail')
            assist = event.get('assist', {}).get('name')
            if assist:
                kinesis_event['metadata']['assist_by'] = assist

        elif event_type == 'foul':
            kinesis_event['metadata']['card_type'] = event.get('detail')

        return kinesis_event

    def send_to_kinesis(self, event: Dict[str, Any]) -> bool:
        """Send event to Kinesis stream"""
        try:
            # Encode as JSON bytes (Kinesis will handle base64 encoding)
            event_json = json.dumps(event)
            event_bytes = event_json.encode('utf-8')

            # Send to Kinesis
            response = kinesis.put_record(
                StreamName=KINESIS_STREAM_NAME,
                Data=event_bytes,
                PartitionKey=event.get('match_id', 'default')
            )

            print(f"  ✅ Sent to Kinesis: {event['event_type']} - {event['player_id']} (Seq: {response['SequenceNumber'][:10]}...)")
            return True

        except Exception as e:
            print(f"  ❌ Failed to send to Kinesis: {e}")
            return False


def main():
    """Main ingestion function"""
    print("=" * 60)
    print("🏆 NPFL Live Data Ingestion - Football Analytics")
    print("=" * 60)
    print()

    if not API_FOOTBALL_KEY:
        print("❌ Error: API_FOOTBALL_KEY not found in config.env")
        sys.exit(1)

    print(f"📡 API Key: {API_FOOTBALL_KEY[:10]}...")
    print(f"🌍 AWS Region: {AWS_REGION}")
    print(f"📊 Kinesis Stream: {KINESIS_STREAM_NAME}")
    print()

    ingestion = NPFLDataIngestion(API_FOOTBALL_KEY)

    # Fetch live fixtures
    print("🔍 Checking for live NPFL matches...")
    live_fixtures = ingestion.fetch_live_fixtures()

    if live_fixtures:
        print(f"\n🎮 Processing {len(live_fixtures)} live matches...")

        for fixture in live_fixtures:
            fixture_id = fixture['fixture']['id']
            home_team = fixture['teams']['home']['name']
            away_team = fixture['teams']['away']['name']
            score = f"{fixture['goals']['home']}-{fixture['goals']['away']}"

            print(f"\n⚽ {home_team} vs {away_team} ({score})")

            # Fetch events for this match
            events = ingestion.fetch_fixture_events(fixture_id)

            if events:
                print(f"  📋 Found {len(events)} events")

                # Transform and send each event
                for event in events:
                    kinesis_event = ingestion.transform_event_to_kinesis_format(event, fixture)
                    ingestion.send_to_kinesis(kinesis_event)
                    time.sleep(0.1)  # Rate limiting
            else:
                print("  ℹ️  No events found for this match")

    else:
        print("\n📅 No live matches. Checking upcoming fixtures...")
        upcoming_fixtures = ingestion.fetch_upcoming_fixtures(days=30)

        if upcoming_fixtures:
            print(f"\n📋 Upcoming NPFL Matches:\n")
            for idx, fixture in enumerate(upcoming_fixtures[:10], 1):
                home_team = fixture['teams']['home']['name']
                away_team = fixture['teams']['away']['name']
                fixture_date = fixture['fixture']['date']
                print(f"  {idx}. {home_team} vs {away_team}")
                print(f"     Date: {fixture_date}")
                print()

            print("💡 Tip: Run this script when matches are live to ingest real-time events")
        else:
            print("ℹ️  No upcoming NPFL matches found")

    print("\n" + "=" * 60)
    print("✅ Ingestion complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
