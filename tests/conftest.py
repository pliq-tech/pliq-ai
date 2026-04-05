"""Integration test fixtures."""

import pytest

from src.config import Config


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    """Config with test values — no real API keys needed."""
    monkeypatch.setenv("GRPC_PORT", "50099")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    return Config()
