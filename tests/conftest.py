"""
Pytest configuration and fixtures for football analytics tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def synthetic_data_dir():
    """Get synthetic data directory."""
    return Path(__file__).parent.parent / "data" / "synthetic"


@pytest.fixture
def sample_match_id():
    """Sample match ID for testing."""
    return "test_match_001"


@pytest.fixture
def sample_team_id():
    """Sample team ID for testing."""
    return "test_team_001"


@pytest.fixture
def sample_player_id():
    """Sample player ID for testing."""
    return "test_player_001"


@pytest.fixture(scope="function")
def mock_aws_credentials(monkeypatch):
    """Mock AWS credentials for testing."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture(scope="function")
def test_config(monkeypatch, tmp_path):
    """Configure test environment."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("USE_LOCALSTACK", "True")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture
def metrics_collector():
    """Get a fresh metrics collector for each test."""
    from src.utils.metrics import MetricsCollector
    return MetricsCollector()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "aws: mark test as requiring AWS services"
    )
