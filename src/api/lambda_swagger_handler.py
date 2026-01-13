"""
Lambda handler for Swagger documentation
Uses Mangum to adapt FastAPI to AWS Lambda
"""

from mangum import Mangum
from swagger_app import app

# Lambda handler
handler = Mangum(app, lifespan="off")
