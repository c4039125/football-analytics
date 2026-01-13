"""Configuration management."""

from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    app_name: str = Field(default="football-analytics-serverless", description="App name")
    app_version: str = Field(default="1.0.0", description="Version")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    aws_region: str = Field(default="us-east-1", description="Region")
    aws_account_id: Optional[str] = Field(None, description="Account ID")

    kinesis_stream_name: str = Field(default="football-analytics-stream", description="Stream name")
    kinesis_shard_count: int = Field(default=4, description="Shard count")
    kinesis_retention_hours: int = Field(default=24, description="Retention hours")

    dynamodb_table_name: str = Field(default="football-analytics", description="Table name")
    dynamodb_read_capacity: int = Field(default=5, description="Read capacity")
    dynamodb_write_capacity: int = Field(default=5, description="Write capacity")

    s3_bucket_name: str = Field(default="football-analytics-data", description="Bucket name")
    s3_prefix: str = Field(default="matches", description="Prefix")

    lambda_memory_size: int = Field(default=512, description="Memory size")
    lambda_timeout: int = Field(default=30, description="Timeout")
    lambda_concurrent_executions: int = Field(default=100, description="Concurrent executions")

    api_gateway_stage: str = Field(default="dev", description="Stage")
    websocket_endpoint: Optional[str] = Field(None, description="WebSocket endpoint")
    api_gateway_throttle_burst: int = Field(default=5000, description="Throttle burst limit")
    api_gateway_throttle_rate: int = Field(default=10000, description="Throttle rate limit")

    # Processing Configuration
    batch_size: int = Field(default=100, description="Event batch size")
    processing_window_seconds: int = Field(default=5, description="Processing window")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_backoff_seconds: int = Field(default=1, description="Retry backoff period")

    # Performance Targets
    target_latency_ms: int = Field(default=500, description="Target end-to-end latency")
    target_throughput: int = Field(default=10000, description="Target events per second")

    # Monitoring Configuration
    enable_xray: bool = Field(default=True, description="Enable AWS X-Ray tracing")
    enable_detailed_metrics: bool = Field(
        default=True,
        description="Enable detailed CloudWatch metrics"
    )
    log_level: str = Field(default="INFO", description="Logging level")

    # Cost Management
    cost_alert_threshold_usd: float = Field(
        default=100.0,
        description="Cost alert threshold"
    )
    enable_cost_tracking: bool = Field(default=True, description="Enable cost tracking")

    # Security
    enable_encryption: bool = Field(default=True, description="Enable encryption")
    kms_key_id: Optional[str] = Field(None, description="KMS key ID for encryption")

    # StatsBomb Configuration
    statsbomb_data_dir: str = Field(
        default="data/raw/statsbomb",
        description="StatsBomb data directory"
    )

    # Testing Configuration
    synthetic_data_enabled: bool = Field(
        default=True,
        description="Enable synthetic data generation"
    )
    test_match_frequency_hz: int = Field(
        default=25,
        description="Test data frequency (Hz)"
    )

    # LocalStack (for local development)
    use_localstack: bool = Field(default=False, description="Use LocalStack for local dev")
    localstack_endpoint: str = Field(
        default="http://localhost:4566",
        description="LocalStack endpoint"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()

    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment. Must be one of {valid_envs}")
        return v.lower()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def aws_endpoint_url(self) -> Optional[str]:
        """Get AWS endpoint URL (for LocalStack)."""
        if self.use_localstack:
            return self.localstack_endpoint
        return None


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
