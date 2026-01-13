/**
 * DynamoDB tables for real-time data storage
 */

# Main analytics table
resource "aws_dynamodb_table" "football_analytics" {
  name           = "${var.project_name}-${var.environment}"
  billing_mode   = var.enable_dynamodb_autoscaling ? "PROVISIONED" : "PAY_PER_REQUEST"
  read_capacity  = var.enable_dynamodb_autoscaling ? var.dynamodb_read_capacity : null
  write_capacity = var.enable_dynamodb_autoscaling ? var.dynamodb_write_capacity : null
  hash_key       = "match_id"
  range_key      = "event_id"

  attribute {
    name = "match_id"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  attribute {
    name = "player_id"
    type = "S"
  }

  attribute {
    name = "team_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  # GSI for player queries
  global_secondary_index {
    name            = "PlayerIndex"
    hash_key        = "player_id"
    range_key       = "timestamp"
    projection_type = "ALL"
    read_capacity   = var.enable_dynamodb_autoscaling ? var.dynamodb_read_capacity : null
    write_capacity  = var.enable_dynamodb_autoscaling ? var.dynamodb_write_capacity : null
  }

  # GSI for team queries
  global_secondary_index {
    name            = "TeamIndex"
    hash_key        = "team_id"
    range_key       = "timestamp"
    projection_type = "ALL"
    read_capacity   = var.enable_dynamodb_autoscaling ? var.dynamodb_read_capacity : null
    write_capacity  = var.enable_dynamodb_autoscaling ? var.dynamodb_write_capacity : null
  }

  # TTL for automatic data expiration
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = var.environment == "production"
  }

  # Server-side encryption
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.football_analytics.arn
  }

  # Streams for change data capture
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-table-${var.environment}"
    }
  )
}

# Auto-scaling for DynamoDB
resource "aws_appautoscaling_target" "dynamodb_read" {
  count              = var.enable_dynamodb_autoscaling ? 1 : 0
  max_capacity       = 20  # Reduced from 100 for cost savings
  min_capacity       = var.dynamodb_read_capacity
  resource_id        = "table/${aws_dynamodb_table.football_analytics.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_read_policy" {
  count              = var.enable_dynamodb_autoscaling ? 1 : 0
  name               = "${var.project_name}-read-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_read[0].resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_read[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_read[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_target" "dynamodb_write" {
  count              = var.enable_dynamodb_autoscaling ? 1 : 0
  max_capacity       = 20  # Reduced from 100 for cost savings
  min_capacity       = var.dynamodb_write_capacity
  resource_id        = "table/${aws_dynamodb_table.football_analytics.name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_write_policy" {
  count              = var.enable_dynamodb_autoscaling ? 1 : 0
  name               = "${var.project_name}-write-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_write[0].resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_write[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_write[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
    target_value = 70.0
  }
}

# CloudWatch alarms
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_throttle" {
  alarm_name          = "${var.project_name}-dynamodb-read-throttle-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "UserErrors"
  namespace           = "AWS/DynamoDB"
  period              = "60"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "DynamoDB read throttle alarm"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    TableName = aws_dynamodb_table.football_analytics.name
  }
}

# Outputs
output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.football_analytics.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.football_analytics.arn
}

output "dynamodb_stream_arn" {
  description = "DynamoDB stream ARN"
  value       = aws_dynamodb_table.football_analytics.stream_arn
}
