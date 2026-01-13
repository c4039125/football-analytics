/**
 * Variables for Football Analytics Serverless Infrastructure
 */

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (development, staging, production)"
  type        = string
  default     = "development"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be development, staging, or production."
  }
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "football-analytics"
}

# Kinesis Configuration
variable "kinesis_shard_count" {
  description = "Number of Kinesis shards"
  type        = number
  default     = 2  # Reduced from 4 for cost savings
}

variable "kinesis_retention_hours" {
  description = "Kinesis data retention in hours"
  type        = number
  default     = 24
}

# Lambda Configuration
variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_concurrent_executions" {
  description = "Lambda reserved concurrent executions"
  type        = number
  default     = 100
}

# DynamoDB Configuration
variable "dynamodb_read_capacity" {
  description = "DynamoDB read capacity units"
  type        = number
  default     = 2  # Reduced from 5 for cost savings
}

variable "dynamodb_write_capacity" {
  description = "DynamoDB write capacity units"
  type        = number
  default     = 2  # Reduced from 5 for cost savings
}

variable "enable_dynamodb_autoscaling" {
  description = "Enable DynamoDB auto-scaling"
  type        = bool
  default     = true
}

# API Gateway Configuration
variable "api_gateway_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 5000
}

variable "api_gateway_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 10000
}

# Monitoring Configuration
variable "enable_xray" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = true
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = true
}

# Cost Management
variable "cost_alert_threshold" {
  description = "Cost alert threshold in USD"
  type        = number
  default     = 100
}

variable "alert_email" {
  description = "Email for alerts"
  type        = string
  default     = "Adebayo.I.Oyeleye@student.shu.ac.uk"
}

# Tags
variable "additional_tags" {
  description = "Additional tags for resources"
  type        = map(string)
  default     = {}
}
