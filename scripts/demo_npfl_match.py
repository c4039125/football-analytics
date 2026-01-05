#!/usr/bin/env python3
"""
Demo NPFL Match Event Generator
Simulates a live NPFL match and sends events to Kinesis
"""

import os
import sys
import json
import base64
import time
import random
from datetime import datetime
from typing import List, Dict, Any
import boto3
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.env'))

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
KINESIS_STREAM_NAME = f"football-analytics-stream-{os.getenv('ENVIRONMENT', 'development')}"

kinesis = boto3.client('kinesis', region_name=AWS_REGION)

# Real NPFL Teams (2024 Season)
NPFL_TEAMS = {
    'enyimba_fc': {
        'name': 'Enyimba FC',
        'players': ['victor_mbaoma', 'chijoke_akuneto', 'akanni_elijah', 'eze_ekwutoziam']
    },
    'rangers_intl': {
        'name': 'Rangers International',
        'players': ['kenechukwu_agu', 'chiamaka_madu', 'isaac_saviour', 'kazeem_ogunleye']
    },
    'plateau_united': {
        'name': 'Plateau United',
        'players': ['jesse_akila', 'mustapha_ibrahim', 'nenrot_silas', 'daniel_itodo']
    },
    'rivers_united': {
        'name': 'Rivers United',
        'players': ['nyima_nwagua', 'kazie_godswill', 'dennis_ndikom', 'alex_oyowah']
    },
    'kano_pillars': {
        'name': 'Kano Pillars',
        'players': ['rabiu_ali', 'nyima_nwagua', 'adamu_hassan', 'usman_mohammed']
    },
    'shooting_stars': {
        'name': 'Shooting Stars SC',
        'players': ['gbolahan_salami', 'ayo_adejubu', 'akilu_muhammed', 'chinedu_udoji']
    }
}

EVENT_TYPES = ['pass', 'shot', 'tackle', 'foul', 'goal']
GOAL_TYPES = ['header', 'right_foot', 'left_foot', 'penalty']


def generate_match_event(match_id: str, minute: int, home_team: str, away_team: str, score: List[int]) -> Dict[str, Any]:
    """Generate a realistic match event"""

    # Randomly choose attacking team
    attacking_team = random.choice([home_team, away_team])
    team_info = NPFL_TEAMS[attacking_team]
    player = random.choice(team_info['players'])

    # Choose event type (goals are rare)
    event_weights = [60, 15, 10, 10, 5]  # pass, shot, tackle, foul, goal
    event_type = random.choices(EVENT_TYPES, weights=event_weights)[0]

    # Random field position
    x = random.randint(0, 100)
    y = random.randint(0, 100)

    event = {
        'event_type': event_type,
        'match_id': match_id,
        'timestamp': datetime.utcnow().isoformat(),
        'team_id': attacking_team,
        'player_id': player,
        'location': {'x': x, 'y': y},
        'metadata': {
            'minute': minute,
            'home_team': NPFL_TEAMS[home_team]['name'],
            'away_team': NPFL_TEAMS[away_team]['name'],
            'score': f"{score[0]}-{score[1]}"
        }
    }

    # Add goal-specific data
    if event_type == 'goal':
        score[0 if attacking_team == home_team else 1] += 1
        event['metadata']['goal_type'] = random.choice(GOAL_TYPES)
        possible_assist = random.choice([p for p in team_info['players'] if p != player])
        event['metadata']['assist_by'] = possible_assist
        event['metadata']['score'] = f"{score[0]}-{score[1]}"

    # Add shot-specific data
    elif event_type == 'shot':
        event['metadata']['on_target'] = random.choice([True, False])
        event['metadata']['shot_type'] = random.choice(['header', 'right_foot', 'left_foot'])

    return event


def send_to_kinesis(event: Dict[str, Any]) -> bool:
    """Send event to Kinesis"""
    try:
        event_json = json.dumps(event)
        event_bytes = event_json.encode('utf-8')

        response = kinesis.put_record(
            StreamName=KINESIS_STREAM_NAME,
            Data=event_bytes,
            PartitionKey=event.get('match_id', 'default')
        )
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def simulate_match(home_team: str, away_team: str, events_per_minute: int = 3, duration_minutes: int = 5):
    """Simulate a live NPFL match"""

    match_id = f"npfl_2024_demo_{int(time.time())}"
    score = [0, 0]

    print("=" * 70)
    print(f"⚽ LIVE MATCH SIMULATION")
    print("=" * 70)
    print(f"🏠 {NPFL_TEAMS[home_team]['name']} vs {NPFL_TEAMS[away_team]['name']} (Away)")
    print(f"🆔 Match ID: {match_id}")
    print(f"⏱️  Duration: {duration_minutes} minutes ({events_per_minute} events/min)")
    print(f"📊 Stream: {KINESIS_STREAM_NAME}")
    print("=" * 70)
    print()

    total_events = 0
    successful_events = 0

    for minute in range(1, duration_minutes + 1):
        print(f"⏰ Minute {minute}")

        for _ in range(events_per_minute):
            event = generate_match_event(match_id, minute, home_team, away_team, score)
            total_events += 1

            # Display event
            icon = "⚽" if event['event_type'] == 'goal' else "🎯" if event['event_type'] == 'shot' else "👟"
            print(f"  {icon} {event['event_type'].upper()}: {event['player_id']} @ ({event['location']['x']}, {event['location']['y']})")

            if event['event_type'] == 'goal':
                print(f"     🎉 GOAL! Score: {score[0]}-{score[1]}")

            # Send to Kinesis
            if send_to_kinesis(event):
                successful_events += 1

            time.sleep(0.3)  # Small delay between events

        print()

    print("=" * 70)
    print(f"✅ Match Complete!")
    print(f"📊 Final Score: {NPFL_TEAMS[home_team]['name']} {score[0]} - {score[1]} {NPFL_TEAMS[away_team]['name']}")
    print(f"📈 Events Generated: {total_events}")
    print(f"✅ Successfully Sent to Kinesis: {successful_events}")
    print(f"❌ Failed: {total_events - successful_events}")
    print("=" * 70)


def main():
    """Main function"""
    print()
    print("🏆 NPFL Match Simulator - Football Analytics Demo")
    print()

    # Pick two random teams
    teams = random.sample(list(NPFL_TEAMS.keys()), 2)
    home_team = teams[0]
    away_team = teams[1]

    # Simulate 5-minute match with 3 events per minute (15 total events)
    simulate_match(home_team, away_team, events_per_minute=3, duration_minutes=5)

    print()
    print("💡 Check your AWS CloudWatch dashboard to see the events processed!")
    print(f"💡 DynamoDB Table: football-analytics-development")
    print()


if __name__ == "__main__":
    main()
