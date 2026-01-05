/**
 * S3 buckets for long-term data storage
 */

# Main data bucket
resource "aws_s3_bucket" "football_analytics_data" {
  bucket = "${var.project_name}-data-${var.environment}-${local.account_id}"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-data-${var.environment}"
    }
  )
}

# Block public access
resource "aws_s3_bucket_public_access_block" "football_analytics_data" {
  bucket = aws_s3_bucket.football_analytics_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning
resource "aws_s3_bucket_versioning" "football_analytics_data" {
  bucket = aws_s3_bucket.football_analytics_data.id

  versioning_configuration {
    status = var.environment == "production" ? "Enabled" : "Suspended"
  }
}

# Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "football_analytics_data" {
  bucket = aws_s3_bucket.football_analytics_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.football_analytics.id
    }
    bucket_key_enabled = true
  }
}

# Lifecycle rules
resource "aws_s3_bucket_lifecycle_configuration" "football_analytics_data" {
  bucket = aws_s3_bucket.football_analytics_data.id

  rule {
    id     = "archive-old-data"
    status = "Enabled"

    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "delete-incomplete-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Logging
resource "aws_s3_bucket_logging" "football_analytics_data" {
  bucket = aws_s3_bucket.football_analytics_data.id

  target_bucket = aws_s3_bucket.logs.id
  target_prefix = "s3-access-logs/"
}

# Logs bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}-${local.account_id}"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-logs-${var.environment}"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    filter {}

    expiration {
      days = 90
    }
  }
}

# Lambda deployment bucket
resource "aws_s3_bucket" "lambda_deployment" {
  bucket = "${var.project_name}-lambda-${var.environment}-${local.account_id}"

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-lambda-${var.environment}"
    }
  )
}

resource "aws_s3_bucket_public_access_block" "lambda_deployment" {
  bucket = aws_s3_bucket.lambda_deployment.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "lambda_deployment" {
  bucket = aws_s3_bucket.lambda_deployment.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Outputs
output "s3_data_bucket_name" {
  description = "S3 data bucket name"
  value       = aws_s3_bucket.football_analytics_data.id
}

output "s3_data_bucket_arn" {
  description = "S3 data bucket ARN"
  value       = aws_s3_bucket.football_analytics_data.arn
}

output "s3_lambda_bucket_name" {
  description = "S3 Lambda deployment bucket name"
  value       = aws_s3_bucket.lambda_deployment.id
}
