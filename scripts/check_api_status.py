#!/usr/bin/env python3
"""
API-Football Connection Checker
Verifies API key and shows available NPFL data
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.env'))

API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
NPFL_LEAGUE_ID = 399


def check_api_status():
    """Check API-Football connection and quota"""
    print("=" * 70)
    print("🔌 API-Football Connection Check")
    print("=" * 70)
    print()

    if not API_FOOTBALL_KEY:
        print("❌ Error: API_FOOTBALL_KEY not found in config.env")
        return False

    print(f"🔑 API Key: {API_FOOTBALL_KEY[:15]}...")
    print()

    headers = {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }

    # Check API status
    try:
        print("⏳ Testing API connection...")
        response = requests.get(f"{API_FOOTBALL_BASE_URL}/status", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'response' in data and data['response']:
            account = data['response']
            print("✅ API Connection Successful!")
            print()
            print("📊 Account Information:")
            print(f"  • Account Name: {account.get('account', {}).get('firstname', 'N/A')} {account.get('account', {}).get('lastname', 'N/A')}")
            print(f"  • Email: {account.get('account', {}).get('email', 'N/A')}")
            print()
            print("📈 API Usage:")
            print(f"  • Requests Today: {account.get('requests', {}).get('current', 0)}")
            print(f"  • Daily Limit: {account.get('requests', {}).get('limit_day', 0)}")
            print(f"  • Remaining: {account.get('requests', {}).get('limit_day', 0) - account.get('requests', {}).get('current', 0)}")
            print()

            # Check NPFL league info
            print("🔍 Checking NPFL (Nigerian Professional Football League)...")
            league_response = requests.get(
                f"{API_FOOTBALL_BASE_URL}/leagues",
                headers=headers,
                params={'id': NPFL_LEAGUE_ID},
                timeout=10
            )

            if league_response.ok:
                league_data = league_response.json()
                if league_data.get('response'):
                    league = league_data['response'][0]
                    print(f"✅ League Found: {league['league']['name']}")
                    print(f"  • Country: {league['country']['name']}")
                    print(f"  • Type: {league['league']['type']}")

                    # Show available seasons
                    if 'seasons' in league:
                        print(f"  • Available Seasons:")
                        for season in league['seasons'][-3:]:  # Last 3 seasons
                            print(f"    - {season['year']}: {season['start']} to {season['end']}")
                else:
                    print("⚠️  NPFL league data not found")
            print()

            # Check for recent/upcoming NPFL fixtures
            print("📅 Checking NPFL Fixtures...")
            fixtures_response = requests.get(
                f"{API_FOOTBALL_BASE_URL}/fixtures",
                headers=headers,
                params={'league': NPFL_LEAGUE_ID, 'season': 2024, 'last': 10},
                timeout=10
            )

            if fixtures_response.ok:
                fixtures_data = fixtures_response.json()
                if fixtures_data.get('response'):
                    fixtures = fixtures_data['response']
                    print(f"✅ Found {len(fixtures)} recent NPFL matches")
                    print()
                    print("Recent Matches:")
                    for idx, fixture in enumerate(fixtures[:5], 1):
                        home = fixture['teams']['home']['name']
                        away = fixture['teams']['away']['name']
                        score_home = fixture['goals']['home']
                        score_away = fixture['goals']['away']
                        status = fixture['fixture']['status']['short']
                        date = fixture['fixture']['date'][:10]

                        print(f"  {idx}. {home} {score_home if score_home is not None else '-'} - {score_away if score_away is not None else '-'} {away}")
                        print(f"     Date: {date} | Status: {status}")
                else:
                    print("ℹ️  No recent NPFL fixtures found")
            print()

            print("=" * 70)
            print("✅ API Check Complete")
            print("💡 Use 'ingest_live_data.py' to fetch live match events")
            print("💡 Use 'demo_npfl_match.py' to simulate a match")
            print("=" * 70)
            return True

        else:
            print("❌ Invalid API response")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ API Connection Failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    check_api_status()
