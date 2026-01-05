/**
 * Kinesis Data Streams for event ingestion
 */

resource "aws_kinesis_stream" "football_analytics" {
  name             = "${var.project_name}-stream-${var.environment}"
  shard_count      = var.kinesis_shard_count
  retention_period = var.kinesis_retention_hours

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds"
  ]

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id      = aws_kms_key.football_analytics.id

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-stream-${var.environment}"
    }
  )
}

# CloudWatch alarms for Kinesis
resource "aws_cloudwatch_metric_alarm" "kinesis_iterator_age" {
  alarm_name          = "${var.project_name}-kinesis-iterator-age-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "60000" # 1 minute
  alarm_description   = "This metric monitors Kinesis iterator age"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.football_analytics.name
  }
}

resource "aws_cloudwatch_metric_alarm" "kinesis_write_throughput" {
  alarm_name          = "${var.project_name}-kinesis-write-throughput-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Kinesis write throughput exceeded"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    StreamName = aws_kinesis_stream.football_analytics.name
  }
}

# Output
output "kinesis_stream_name" {
  description = "Kinesis stream name"
  value       = aws_kinesis_stream.football_analytics.name
}

output "kinesis_stream_arn" {
  description = "Kinesis stream ARN"
  value       = aws_kinesis_stream.football_analytics.arn
}
