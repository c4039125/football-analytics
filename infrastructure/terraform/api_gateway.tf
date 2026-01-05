/**
 * API Gateway for REST and WebSocket APIs
 */

# IAM role for API Gateway logging
resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.project_name}-api-gateway-cloudwatch-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Set API Gateway account settings (required for logging)
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

# REST API
resource "aws_apigatewayv2_api" "rest_api" {
  name          = "${var.project_name}-rest-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "Football Analytics REST API"

  cors_configuration {
    allow_origins = var.environment == "production" ? ["https://yourdomain.com"] : ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    max_age       = 300
  }

  tags = local.common_tags
}

# REST API Stage
resource "aws_apigatewayv2_stage" "rest_api" {
  api_id      = aws_apigatewayv2_api.rest_api.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.api_gateway_throttle_burst_limit
    throttling_rate_limit  = var.api_gateway_throttle_rate_limit
  }

  depends_on = [aws_api_gateway_account.main]

  tags = local.common_tags
}

# Lambda function for API Handler (Swagger docs)
resource "aws_lambda_function" "api_handler" {
  function_name = "${var.project_name}-api-handler-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "api.combined_api_handler.handler"
  runtime       = local.lambda_runtime

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  memory_size = 512
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT    = var.environment
      DYNAMODB_TABLE = aws_dynamodb_table.football_analytics.name
    }
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-api-handler-${var.environment}"
    }
  )
}

# CloudWatch Log Group for API Handler
resource "aws_cloudwatch_log_group" "api_handler" {
  name              = "/aws/lambda/${aws_lambda_function.api_handler.function_name}"
  retention_in_days = 1

  kms_key_id = aws_kms_key.football_analytics.arn

  tags = local.common_tags
}

# API Gateway Integration for API Handler
resource "aws_apigatewayv2_integration" "api_handler" {
  api_id = aws_apigatewayv2_api.rest_api.id

  integration_uri    = aws_lambda_function.api_handler.invoke_arn
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  payload_format_version = "2.0"
}

# API Gateway Routes for API Handler
resource "aws_apigatewayv2_route" "api_handler_root" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "GET /"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_handler_health" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_handler_docs" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "GET /docs"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_handler_redoc" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "GET /redoc"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_handler_openapi" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "GET /openapi.json"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_handler_catchall" {
  api_id    = aws_apigatewayv2_api.rest_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.rest_api.execution_arn}/*/*"
}

# WebSocket API
resource "aws_apigatewayv2_api" "websocket_api" {
  name                       = "${var.project_name}-websocket-api-${var.environment}"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  description                = "Football Analytics WebSocket API for real-time updates"

  tags = local.common_tags
}

# WebSocket Stage
resource "aws_apigatewayv2_stage" "websocket_api" {
  api_id      = aws_apigatewayv2_api.websocket_api.id
  name        = var.environment
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_websocket.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      connectionId   = "$context.connectionId"
      eventType      = "$context.eventType"
      status         = "$context.status"
    })
  }

  default_route_settings {
    throttling_burst_limit = var.api_gateway_throttle_burst_limit
    throttling_rate_limit  = var.api_gateway_throttle_rate_limit
  }

  depends_on = [aws_api_gateway_account.main]

  tags = local.common_tags
}

# Lambda function for WebSocket connections
resource "aws_lambda_function" "websocket_handler" {
  function_name = "${var.project_name}-websocket-handler-${var.environment}"
  role          = aws_iam_role.lambda_execution.arn
  handler       = "delivery.websocket_handler.lambda_handler"
  runtime       = local.lambda_runtime

  filename         = "lambda_placeholder.zip"
  source_code_hash = filebase64sha256("lambda_placeholder.zip")

  memory_size = 256
  timeout     = 30

  environment {
    variables = {
      ENVIRONMENT      = var.environment
      DYNAMODB_TABLE   = aws_dynamodb_table.football_analytics.name
      WEBSOCKET_API_ID = aws_apigatewayv2_api.websocket_api.id
      STAGE            = var.environment
    }
  }

  tracing_config {
    mode = var.enable_xray ? "Active" : "PassThrough"
  }

  tags = local.common_tags
}

# WebSocket routes
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket_api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.websocket_default.id}"
}

# WebSocket integrations
resource "aws_apigatewayv2_integration" "websocket_connect" {
  api_id           = aws_apigatewayv2_api.websocket_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_disconnect" {
  api_id           = aws_apigatewayv2_api.websocket_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "websocket_default" {
  api_id           = aws_apigatewayv2_api.websocket_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.websocket_handler.invoke_arn
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "websocket_connect" {
  statement_id  = "AllowExecutionFromAPIGatewayConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/$connect"
}

resource "aws_lambda_permission" "websocket_disconnect" {
  statement_id  = "AllowExecutionFromAPIGatewayDisconnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/$disconnect"
}

resource "aws_lambda_permission" "websocket_default" {
  statement_id  = "AllowExecutionFromAPIGatewayDefault"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.websocket_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket_api.execution_arn}/*/$default"
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-rest-${var.environment}"
  retention_in_days = 1  # Reduced from 7 for cost savings
  kms_key_id        = aws_kms_key.football_analytics.arn

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "api_gateway_websocket" {
  name              = "/aws/apigateway/${var.project_name}-websocket-${var.environment}"
  retention_in_days = 1  # Reduced from 7 for cost savings
  kms_key_id        = aws_kms_key.football_analytics.arn

  tags = local.common_tags
}

# Outputs
output "rest_api_endpoint" {
  description = "REST API endpoint"
  value       = aws_apigatewayv2_stage.rest_api.invoke_url
}

output "websocket_api_endpoint" {
  description = "WebSocket API endpoint"
  value       = aws_apigatewayv2_stage.websocket_api.invoke_url
}

output "websocket_api_id" {
  description = "WebSocket API ID"
  value       = aws_apigatewayv2_api.websocket_api.id
}
