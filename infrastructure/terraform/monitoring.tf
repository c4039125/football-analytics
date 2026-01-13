/**
 * Monitoring and alerting resources
 */

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-alerts-${var.environment}"
  kms_master_key_id = aws_kms_key.football_analytics.id

  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", { stat = "Sum", label = "Kinesis Incoming Records" }],
            [".", "IncomingBytes", { stat = "Sum", label = "Kinesis Incoming Bytes" }]
          ]
          period = 300
          stat   = "Sum"
          region = local.region
          title  = "Kinesis Ingestion Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { stat = "Sum", label = "Lambda Invocations" }],
            [".", "Errors", { stat = "Sum", label = "Lambda Errors" }],
            [".", "Duration", { stat = "Average", label = "Lambda Duration" }]
          ]
          period = 300
          stat   = "Average"
          region = local.region
          title  = "Lambda Processing Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { stat = "Sum" }],
            [".", "ConsumedWriteCapacityUnits", { stat = "Sum" }]
          ]
          period = 300
          stat   = "Sum"
          region = local.region
          title  = "DynamoDB Capacity Metrics"
        }
      }
    ]
  })
}

# Custom CloudWatch metrics
resource "aws_cloudwatch_log_metric_filter" "processing_latency" {
  name           = "${var.project_name}-processing-latency-${var.environment}"
  log_group_name = aws_cloudwatch_log_group.event_processor.name
  pattern        = "[timestamp, request_id, level, message, processing_time_ms]"

  metric_transformation {
    name      = "ProcessingLatency"
    namespace = "FootballAnalytics"
    value     = "$processing_time_ms"
    unit      = "Milliseconds"
  }
}

# Budget alerts
resource "aws_budgets_budget" "monthly_cost" {
  name              = "${var.project_name}-monthly-budget-${var.environment}"
  budget_type       = "COST"
  limit_amount      = var.cost_alert_threshold
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }
}

# Application Performance alarms
resource "aws_cloudwatch_metric_alarm" "end_to_end_latency" {
  alarm_name          = "${var.project_name}-e2e-latency-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ProcessingLatency"
  namespace           = "FootballAnalytics"
  period              = "60"
  statistic           = "Average"
  threshold           = "500" # 500ms target
  alarm_description   = "End-to-end latency exceeds target"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  tags = local.common_tags
}

# X-Ray sampling rule
resource "aws_xray_sampling_rule" "football_analytics" {
  count = var.enable_xray ? 1 : 0

  rule_name      = "${var.project_name}-${var.environment}"
  priority       = 1000
  version        = 1
  reservoir_size = 1
  fixed_rate     = var.environment == "production" ? 0.05 : 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "${var.project_name}-*"
  resource_arn   = "*"

  attributes = {
    Environment = var.environment
  }
}

# Outputs
output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${local.region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = aws_sns_topic.alerts.arn
}
