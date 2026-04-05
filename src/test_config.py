"""Unit tests for src.config.Config."""

import os

import pytest
from pydantic import ValidationError

from src.config import Config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove config-related env vars before each test to ensure isolation."""
    env_keys = [
        "GRPC_HOST",
        "GRPC_PORT",
        "MAX_WORKERS",
        "GOOGLE_API_KEY",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_LOCATION",
        "GEMINI_PRO_MODEL",
        "GEMINI_FLASH_MODEL",
        "EMBEDDING_MODEL",
        "FRAUD_ELA_WEIGHT",
        "FRAUD_FFT_WEIGHT",
        "FRAUD_EXIF_WEIGHT",
        "FRAUD_REVERSE_WEIGHT",
        "FRAUD_DETECTION_THRESHOLD",
        "PRICE_ANOMALY_Z_THRESHOLD",
        "DUPLICATION_TEXT_THRESHOLD",
        "DUPLICATION_PHASH_THRESHOLD",
        "COMMUTE_WEIGHT",
        "NOISE_WEIGHT",
        "AMENITY_WEIGHT",
        "SOCIAL_WEIGHT",
        "BUDGET_WEIGHT",
        "PET_WEIGHT",
        "LOG_LEVEL",
    ]
    for key in env_keys:
        monkeypatch.delenv(key, raising=False)


def test_valid_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config.from_env() succeeds when required env vars are set."""
    # Arrange
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-123")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")

    # Act
    config = Config.from_env()

    # Assert
    assert config.google_api_key == "test-key-123"
    assert config.google_project_id == "test-project"


def test_missing_google_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """Config.from_env() raises ValidationError when GOOGLE_API_KEY is missing."""
    # Arrange — GOOGLE_API_KEY not set (cleaned by fixture)

    # Act & Assert
    with pytest.raises(ValidationError):
        Config.from_env()


def test_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """All fields with defaults use the correct default values."""
    # Arrange
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")

    # Act
    config = Config.from_env()

    # Assert — server defaults
    assert config.grpc_host == "0.0.0.0"
    assert config.grpc_port == 50051
    assert config.max_workers == 10

    # Assert — Google AI defaults
    assert config.google_location == "us-central1"
    assert config.google_project_id == ""

    # Assert — model defaults
    assert config.gemini_pro_model == "gemini-2.5-pro-preview-05-06"
    assert config.gemini_flash_model == "gemini-2.5-flash-preview-05-20"
    assert config.embedding_model == "text-embedding-005"

    # Assert — fraud detection defaults
    assert config.fraud_ela_weight == 0.35
    assert config.fraud_fft_weight == 0.25
    assert config.fraud_exif_weight == 0.20
    assert config.fraud_reverse_weight == 0.20
    assert config.fraud_detection_threshold == 0.7
    assert config.price_anomaly_z_threshold == 2.0
    assert config.duplication_text_threshold == 0.85
    assert config.duplication_phash_threshold == 10

    # Assert — matching weight defaults
    assert config.commute_weight == 0.25
    assert config.noise_weight == 0.15
    assert config.amenity_weight == 0.15
    assert config.social_weight == 0.10
    assert config.budget_weight == 0.25
    assert config.pet_weight == 0.10

    # Assert — logging default
    assert config.log_level == "info"


def test_env_overrides_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override default field values."""
    # Arrange
    monkeypatch.setenv("GOOGLE_API_KEY", "key")
    monkeypatch.setenv("GRPC_PORT", "9999")
    monkeypatch.setenv("COMMUTE_WEIGHT", "0.40")
    monkeypatch.setenv("PRICE_ANOMALY_Z_THRESHOLD", "3.5")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Act
    config = Config.from_env()

    # Assert
    assert config.grpc_port == 9999
    assert config.commute_weight == 0.40
    assert config.price_anomaly_z_threshold == 3.5
    assert config.log_level == "DEBUG"
