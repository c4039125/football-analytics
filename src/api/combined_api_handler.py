"""
Combined API handler for both health checks and Swagger documentation
Uses Mangum to adapt FastAPI to AWS Lambda
"""

import logging
from mangum import Mangum
from api.swagger_app import app

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lambda handler using Mangum adapter
# This allows the FastAPI app to run on AWS Lambda
handler = Mangum(app, lifespan="off", api_gateway_base_path="/development")
