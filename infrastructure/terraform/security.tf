/**
 * Security resources (KMS, IAM, etc.)
 */

# KMS key for encryption
resource "aws_kms_key" "football_analytics" {
  description             = "KMS key for Football Analytics encryption"
  deletion_window_in_days = var.environment == "production" ? 30 : 7
  enable_key_rotation     = true

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-kms-${var.environment}"
    }
  )
}

resource "aws_kms_alias" "football_analytics" {
  name          = "alias/${var.project_name}-${var.environment}"
  target_key_id = aws_kms_key.football_analytics.key_id
}

# KMS key policy
resource "aws_kms_key_policy" "football_analytics" {
  key_id = aws_kms_key.football_analytics.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${local.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow services to use the key"
        Effect = "Allow"
        Principal = {
          Service = [
            "kinesis.amazonaws.com",
            "dynamodb.amazonaws.com",
            "s3.amazonaws.com",
            "lambda.amazonaws.com",
            "cloudwatch.amazonaws.com",
            "sqs.amazonaws.com"
          ]
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = "*"
      },
      {
        Sid    = "Allow CloudWatch Logs"
        Effect = "Allow"
        Principal = {
          Service = "logs.${data.aws_region.current.name}.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:GenerateDataKey",
          "kms:CreateGrant",
          "kms:DescribeKey"
        ]
        Resource = "*"
        Condition = {
          ArnLike = {
            "kms:EncryptionContext:aws:logs:arn" = "arn:aws:logs:${data.aws_region.current.name}:${local.account_id}:*"
          }
        }
      }
    ]
  })
}

# Secrets Manager for sensitive configuration
resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "${var.project_name}/api-keys/${var.environment}"
  description             = "API keys and sensitive configuration"
  recovery_window_in_days = var.environment == "production" ? 30 : 0
  kms_key_id              = aws_kms_key.football_analytics.id

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    statsbomb_api_key = "placeholder"
    # Add other secrets as needed
  })
}

# Output
output "kms_key_id" {
  description = "KMS key ID"
  value       = aws_kms_key.football_analytics.id
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = aws_kms_key.football_analytics.arn
}
