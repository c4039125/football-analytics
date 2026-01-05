/**
 * Terraform outputs
 */

output "summary" {
  description = "Deployment summary"
  value = {
    environment = var.environment
    region      = local.region
    project     = var.project_name
  }
}

output "endpoints" {
  description = "API endpoints"
  value = {
    rest_api       = aws_apigatewayv2_stage.rest_api.invoke_url
    websocket_api  = aws_apigatewayv2_stage.websocket_api.invoke_url
    dashboard_url  = "https://console.aws.amazon.com/cloudwatch/home?region=${local.region}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
  }
}

output "resource_arns" {
  description = "Resource ARNs"
  value = {
    kinesis_stream   = aws_kinesis_stream.football_analytics.arn
    dynamodb_table   = aws_dynamodb_table.football_analytics.arn
    s3_data_bucket   = aws_s3_bucket.football_analytics_data.arn
    lambda_function  = aws_lambda_function.event_processor.arn
    kms_key          = aws_kms_key.football_analytics.arn
  }
}

output "resource_names" {
  description = "Resource names"
  value = {
    kinesis_stream  = aws_kinesis_stream.football_analytics.name
    dynamodb_table  = aws_dynamodb_table.football_analytics.name
    s3_data_bucket  = aws_s3_bucket.football_analytics_data.id
    lambda_function = aws_lambda_function.event_processor.function_name
  }
}
