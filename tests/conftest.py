"""Integration test fixtures."""

import io

import pytest
from PIL import Image

from src.config import Config


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    """Config with test values -- no real API keys needed."""
    monkeypatch.setenv("GRPC_PORT", "50099")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    return Config.from_env()


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a simple synthetic test image as JPEG bytes."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=95)
    return buffer.getvalue()


@pytest.fixture
def mock_grpc_context():
    """Mock gRPC service context for handler tests."""

    class MockContext:
        def __init__(self):
            self._code = None
            self._details = None

        def set_code(self, code):
            self._code = code

        def set_details(self, details):
            self._details = details

        async def abort(self, code, details):
            self._code = code
            self._details = details
            raise Exception(f"gRPC abort: {code} {details}")

        def invocation_metadata(self):
            return [("x-request-id", "test-req-001")]

    return MockContext()
