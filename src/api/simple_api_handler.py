"""
Simple API handler for API Gateway.
"""

import json
from datetime import datetime


def lambda_handler(event, context):
    """
    Simple API handler for health checks and basic queries.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        dict: API response
    """

    # Extract request details
    path = event.get('rawPath', event.get('path', '/'))
    method = event.get('requestContext', {}).get('http', {}).get('method',
                event.get('httpMethod', 'GET'))

    # Strip stage name from path (e.g., /development/health -> /health)
    path_parts = path.split('/')
    if len(path_parts) > 2 and path_parts[1] == 'development':
        path = '/' + '/'.join(path_parts[2:])
    if path == '':
        path = '/'

    # Route handling
    if path == '/health' or path == '/':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'healthy',
                'service': 'football-analytics-api',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'message': 'Football Analytics System is running!',
                'endpoints': {
                    'health': '/health',
                    'docs': 'API documentation coming soon'
                }
            })
        }

    # Default 404 for unknown paths
    return {
        'statusCode': 404,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': 'Not Found',
            'path': path,
            'message': 'Available endpoints: /health'
        })
    }
