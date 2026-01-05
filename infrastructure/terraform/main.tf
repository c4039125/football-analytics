/**
 * Main Terraform configuration for Football Analytics Serverless System
 *
 * This creates a complete serverless infrastructure on AWS including:
 * - Kinesis Data Streams for ingestion
 * - Lambda functions for processing
 * - DynamoDB for real-time storage
 * - S3 for long-term storage
 * - API Gateway for delivery
 * - CloudWatch for monitoring
 */

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Backend configuration for state management
  # Using local backend for initial deployment
  # Uncomment below to use S3 backend (after creating the bucket)
  # backend "s3" {
  #   bucket         = "football-analytics-terraform-state"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "football-analytics-terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FootballAnalytics"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Adebayo Oyeleye"
      Research    = "MSc Computing"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local variables
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  common_tags = {
    Project     = "FootballAnalytics"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  lambda_runtime = "python3.11"
}
