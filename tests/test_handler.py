"""Tests for the API request handler."""
import pytest

from src.backend.api.handler import RequestHandler
from tests.config import VALIDATION_ENABLED


@pytest.fixture
def handler():
    """Create a RequestHandler instance for testing."""
    config = {"api_key": "test-key", "timeout": 30}
    return RequestHandler(config)


def test_process_request(handler):
    """Test processing a valid request."""
    data = {"id": "123", "type": "test", "value": "data"}
    result = handler.process_request(data)

    assert result["status"] == "success"
    assert result["data"] == data


def test_validate_request_valid(handler):
    """Test validation with valid data."""
    data = {"id": "123", "type": "test"}
    assert handler.validate_request(data) is True


def test_validate_request_missing_id(handler):
    """Test validation with missing id."""
    data = {"type": "test"}
    assert handler.validate_request(data) is False


def test_validate_request_missing_type(handler):
    """Test validation with missing type."""
    data = {"id": "123"}
    assert handler.validate_request(data) is False


def test_validation_enabled():
    """Test that validation is enabled.

    This test can be toggled by changing VALIDATION_ENABLED in tests/config.py:
    - VALIDATION_ENABLED = True  -> test passes
    - VALIDATION_ENABLED = False -> test fails
    """
    assert VALIDATION_ENABLED is True, "Validation must be enabled"
