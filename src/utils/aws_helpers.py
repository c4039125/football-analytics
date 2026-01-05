"""
AWS service client helpers and utilities.
"""

import boto3
from typing import Optional
from botocore.config import Config
from functools import lru_cache

from .config import get_settings
from .logger import get_logger

logger = get_logger(__name__)


def get_boto_config() -> Config:
    """
    Get boto3 configuration.

    Returns:
        Config: Boto3 configuration
    """
    settings = get_settings()

    return Config(
        region_name=settings.aws_region,
        retries={
            'max_attempts': settings.max_retries,
            'mode': 'adaptive'
        },
        max_pool_connections=50,
    )


@lru_cache()
def get_kinesis_client():
    """
    Get Kinesis client.

    Returns:
        boto3.client: Kinesis client
    """
    settings = get_settings()
    logger.info("Initializing Kinesis client", region=settings.aws_region)

    return boto3.client(
        'kinesis',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


@lru_cache()
def get_dynamodb_client():
    """
    Get DynamoDB client.

    Returns:
        boto3.client: DynamoDB client
    """
    settings = get_settings()
    logger.info("Initializing DynamoDB client", region=settings.aws_region)

    return boto3.client(
        'dynamodb',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


@lru_cache()
def get_dynamodb_resource():
    """
    Get DynamoDB resource.

    Returns:
        boto3.resource: DynamoDB resource
    """
    settings = get_settings()

    return boto3.resource(
        'dynamodb',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


@lru_cache()
def get_s3_client():
    """
    Get S3 client.

    Returns:
        boto3.client: S3 client
    """
    settings = get_settings()
    logger.info("Initializing S3 client", region=settings.aws_region)

    return boto3.client(
        's3',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


@lru_cache()
def get_api_gateway_client():
    """
    Get API Gateway Management API client.

    Returns:
        boto3.client: API Gateway Management client
    """
    settings = get_settings()
    logger.info("Initializing API Gateway client")

    # For WebSocket, we need the management API
    return boto3.client(
        'apigatewaymanagementapi',
        endpoint_url=settings.websocket_endpoint,
        config=get_boto_config()
    )


@lru_cache()
def get_cloudwatch_client():
    """
    Get CloudWatch client.

    Returns:
        boto3.client: CloudWatch client
    """
    settings = get_settings()
    logger.info("Initializing CloudWatch client")

    return boto3.client(
        'cloudwatch',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


@lru_cache()
def get_lambda_client():
    """
    Get Lambda client.

    Returns:
        boto3.client: Lambda client
    """
    settings = get_settings()
    logger.info("Initializing Lambda client")

    return boto3.client(
        'lambda',
        endpoint_url=settings.aws_endpoint_url,
        config=get_boto_config()
    )


def parse_kinesis_record(record: dict) -> Optional[dict]:
    """
    Parse a Kinesis record.

    Args:
        record: Kinesis record

    Returns:
        dict: Parsed data, or None if parsing fails
    """
    import base64
    import json

    try:
        # Kinesis data is base64 encoded
        data = base64.b64decode(record['kinesis']['data'])
        return json.loads(data)
    except Exception as e:
        logger.error(f"Failed to parse Kinesis record", error=str(e))
        return None


def parse_dynamodb_record(record: dict) -> Optional[dict]:
    """
    Parse a DynamoDB stream record.

    Args:
        record: DynamoDB stream record

    Returns:
        dict: Parsed data, or None if parsing fails
    """
    from boto3.dynamodb.types import TypeDeserializer

    try:
        deserializer = TypeDeserializer()

        if record['eventName'] == 'INSERT' or record['eventName'] == 'MODIFY':
            # Get the new image
            new_image = record['dynamodb']['NewImage']
            return {k: deserializer.deserialize(v) for k, v in new_image.items()}
        elif record['eventName'] == 'REMOVE':
            # Get the old image
            old_image = record['dynamodb']['OldImage']
            return {k: deserializer.deserialize(v) for k, v in old_image.items()}

        return None
    except Exception as e:
        logger.error(f"Failed to parse DynamoDB record", error=str(e))
        return None


def batch_write_dynamodb(table_name: str, items: list, max_batch_size: int = 25):
    """
    Batch write items to DynamoDB.

    Args:
        table_name: DynamoDB table name
        items: List of items to write
        max_batch_size: Maximum batch size (DynamoDB limit is 25)
    """
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(table_name)

    # Split into batches
    for i in range(0, len(items), max_batch_size):
        batch = items[i:i + max_batch_size]

        with table.batch_writer() as writer:
            for item in batch:
                writer.put_item(Item=item)

        logger.info(f"Wrote batch of {len(batch)} items to DynamoDB")


def put_kinesis_records(stream_name: str, records: list):
    """
    Put records to Kinesis stream.

    Args:
        stream_name: Kinesis stream name
        records: List of records (each with 'Data' and 'PartitionKey')

    Returns:
        dict: PutRecords response
    """
    client = get_kinesis_client()

    try:
        response = client.put_records(
            StreamName=stream_name,
            Records=records
        )

        failed_count = response.get('FailedRecordCount', 0)
        if failed_count > 0:
            logger.warning(
                f"Failed to put {failed_count} records to Kinesis",
                stream=stream_name
            )

        return response
    except Exception as e:
        logger.error(f"Failed to put records to Kinesis", error=str(e))
        raise


def put_cloudwatch_metric(
    namespace: str,
    metric_name: str,
    value: float,
    unit: str = 'Count',
    dimensions: Optional[dict] = None
):
    """
    Put a metric to CloudWatch.

    Args:
        namespace: Metric namespace
        metric_name: Metric name
        value: Metric value
        unit: Metric unit
        dimensions: Metric dimensions
    """
    client = get_cloudwatch_client()

    metric_data = {
        'MetricName': metric_name,
        'Value': value,
        'Unit': unit,
    }

    if dimensions:
        metric_data['Dimensions'] = [
            {'Name': k, 'Value': v} for k, v in dimensions.items()
        ]

    try:
        client.put_metric_data(
            Namespace=namespace,
            MetricData=[metric_data]
        )
    except Exception as e:
        logger.error(f"Failed to put CloudWatch metric", error=str(e))
