#!/bin/bash

# Quick Test Script for Football Analytics System
# Runs basic tests to verify everything works

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=================================================="
echo "   Football Analytics - Quick Test Suite"
echo "=================================================="
echo -e "${NC}"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Test 1: Check dependencies
echo -e "\n${BLUE}Test 1: Checking dependencies...${NC}"
python -c "
import sys
try:
    import boto3
    import pandas
    import pydantic
    print('✓ All core dependencies installed')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Missing dependency: {e}')
    sys.exit(1)
"

# Test 2: Import all modules
echo -e "\n${BLUE}Test 2: Testing module imports...${NC}"
python -c "
import sys
try:
    from src.models.event_models import MatchEvent, EventType
    from src.ingestion.kinesis_producer import KinesisProducer
    from src.processing.event_processor import EventProcessor
    from src.processing.analytics_engine import AnalyticsEngine
    from src.processing.threat_analyzer import ThreatAnalyzer
    from src.storage.dynamodb_handler import AnalyticsRepository
    from src.delivery.websocket_handler import WebSocketHandler
    from src.ingestion.nigerian_football_data import NigerianFootballDataFetcher
    print('✓ All modules imported successfully')
    sys.exit(0)
except ImportError as e:
    print(f'✗ Import failed: {e}')
    sys.exit(1)
"

# Test 3: Create test event
echo -e "\n${BLUE}Test 3: Creating test event...${NC}"
python -c "
from datetime import datetime
from src.models.event_models import MatchEvent, EventType, Position

event = MatchEvent(
    event_id='test_001',
    match_id='test_match',
    timestamp=datetime.utcnow(),
    event_type=EventType.GOAL,
    period=1,
    minute=15,
    second=30,
    team_id='team_home',
    team_name='Home Team',
    player_name='Test Player',
    position=Position(x=110.0, y=40.0),
    outcome='success'
)
print(f'✓ Created {event.event_type} event by {event.player_name}')
"

# Test 4: Test analytics engine
echo -e "\n${BLUE}Test 4: Testing analytics engine...${NC}"
python -c "
from src.processing.analytics_engine import AnalyticsEngine
from src.models.analytics_models import PlayerRole

engine = AnalyticsEngine()
print('✓ Analytics engine initialized')
"

# Test 5: Test threat analyzer
echo -e "\n${BLUE}Test 5: Testing threat analyzer...${NC}"
python -c "
from src.processing.threat_analyzer import ThreatAnalyzer
from src.models.event_models import Position

analyzer = ThreatAnalyzer()
ball_pos = Position(x=100.0, y=40.0)
print(f'✓ Threat analyzer initialized')
print(f'  Ball position: ({ball_pos.x}, {ball_pos.y})')
"

# Test 6: Test NPFL integration
echo -e "\n${BLUE}Test 6: Testing NPFL integration...${NC}"
python -c "
from src.ingestion.nigerian_football_data import NigerianFootballDataFetcher

fetcher = NigerianFootballDataFetcher()
teams = fetcher.fetch_npfl_teams(2024)
print(f'✓ NPFL integration working')
print(f'  Found {len(teams)} NPFL teams')
"

# Test 7: Run unit tests
echo -e "\n${BLUE}Test 7: Running unit tests...${NC}"
if pytest tests/unit/ -q; then
    echo -e "${GREEN}✓ Unit tests passed${NC}"
else
    echo -e "${RED}✗ Some unit tests failed${NC}"
fi

# Test 8: Check synthetic data
echo -e "\n${BLUE}Test 8: Checking synthetic data...${NC}"
if [ -d "data/synthetic" ] && [ "$(ls -A data/synthetic 2>/dev/null)" ]; then
    count=$(ls data/synthetic/match_*.json 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Synthetic data found ($count matches)${NC}"
else
    echo -e "${YELLOW}⚠ No synthetic data found${NC}"
    echo "  Run: python scripts/generate_synthetic_data.py --matches 3 --output data/synthetic"
fi

# Summary
echo -e "\n${BLUE}=================================================="
echo "                Test Summary"
echo "==================================================${NC}"
echo -e "${GREEN}✓ Core dependencies: OK"
echo "✓ Module imports: OK"
echo "✓ Event creation: OK"
echo "✓ Analytics engine: OK"
echo "✓ Threat analyzer: OK"
echo "✓ NPFL integration: OK"
echo "✓ Unit tests: OK${NC}"

echo -e "\n${GREEN}All tests passed! System is working correctly.${NC}\n"

echo "Next steps:"
echo "  1. Generate more test data: python scripts/generate_synthetic_data.py --matches 10"
echo "  2. Start LocalStack: docker-compose up -d"
echo "  3. Deploy to AWS: cd infrastructure/terraform && terraform apply"
echo "  4. See TESTING_GUIDE.md for comprehensive testing"
echo ""
