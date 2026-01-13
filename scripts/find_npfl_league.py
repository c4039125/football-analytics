#!/usr/bin/env python3
"""Find the correct NPFL league ID in API-Football"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.env'))

API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY')
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"

headers = {
    'x-rapidapi-key': API_FOOTBALL_KEY,
    'x-rapidapi-host': 'v3.football.api-sports.io'
}

print("🔍 Searching for Nigerian football leagues...")
print()

# Search for Nigeria
response = requests.get(
    f"{API_FOOTBALL_BASE_URL}/leagues",
    headers=headers,
    params={'country': 'Nigeria'},
    timeout=10
)

if response.ok:
    data = response.json()
    if data.get('response'):
        print(f"✅ Found {len(data['response'])} Nigerian leagues:")
        print()
        for league_data in data['response']:
            league = league_data['league']
            country = league_data['country']
            print(f"ID: {league['id']}")
            print(f"  • Name: {league['name']}")
            print(f"  • Type: {league['type']}")
            print(f"  • Country: {country['name']}")
            if 'seasons' in league_data:
                seasons = [s['year'] for s in league_data['seasons']]
                print(f"  • Available Seasons: {seasons}")
            print()
    else:
        print("❌ No Nigerian leagues found")
else:
    print(f"❌ API Error: {response.status_code}")
