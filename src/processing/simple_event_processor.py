"""
Simple event processor for Lambda - minimal dependencies for demo.
"""

import json
import base64
import boto3
from datetime import datetime

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')


def lambda_handler(event, context):
    """
    Process Kinesis events and store in DynamoDB.

    Args:
        event: Kinesis event
        context: Lambda context

    Returns:
        dict: Processing result
    """
    processed_count = 0
    errors = []

    # Get table name from environment variable
    import os
    table_name = os.environ.get('DYNAMODB_TABLE', 'football-analytics-development')
    table = dynamodb.Table(table_name)

    for record in event.get('Records', []):
        try:
            # Decode Kinesis data (handle both string and bytes)
            kinesis_data = record['kinesis']['data']

            # If data is already a string (pre-decoded by Lambda), use it directly
            if isinstance(kinesis_data, str):
                try:
                    # Try to parse as JSON directly
                    event_data = json.loads(kinesis_data)
                except:
                    # If that fails, try base64 decode then JSON
                    data = base64.b64decode(kinesis_data)
                    event_data = json.loads(data.decode('utf-8'))
            else:
                # If bytes, decode directly
                event_data = json.loads(kinesis_data.decode('utf-8'))

            # Add processing metadata
            event_data['processed_at'] = datetime.utcnow().isoformat()
            event_data['sequence_number'] = record['kinesis']['sequenceNumber']
            event_data['partition_key'] = record['kinesis']['partitionKey']

            # Create primary key
            event_id = f"{event_data.get('match_id', 'unknown')}_{record['kinesis']['sequenceNumber']}"
            event_data['event_id'] = event_id
            event_data['timestamp'] = event_data.get('timestamp', datetime.utcnow().isoformat())

            # Store in DynamoDB
            table.put_item(Item=event_data)

            processed_count += 1
            print(f"✅ Processed event: {event_id}")

        except Exception as e:
            error_msg = f"Error processing record: {str(e)}"
            errors.append(error_msg)
            print(f"❌ {error_msg}")

    result = {
        'processed': processed_count,
        'errors': len(errors),
        'error_details': errors[:10]  # Limit error details
    }

    print(f"📊 Summary: {result}")

    return result
