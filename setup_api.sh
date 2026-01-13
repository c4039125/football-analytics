#!/bin/bash

echo "Setting up Football Analytics API..."
echo ""

cd /Users/mac/Documents/Work/Adebayo_Research/football-analytics-serverless

# Create virtual environment if it doesn't exist
if [ ! -d "env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Install FastAPI and uvicorn
echo "Installing FastAPI and dependencies..."
pip install fastapi uvicorn python-multipart structlog pydantic-settings boto3 requests aws-lambda-powertools

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the API:"
echo "  1. source env/bin/activate"
echo "  2. python run_api.py"
echo ""
echo "Then open: http://localhost:8002/docs"
echo ""
