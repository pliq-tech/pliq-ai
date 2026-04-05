"""Root conftest for pliq-ai test suite."""

import io

import pytest
from PIL import Image

from src.config import Config


@pytest.fixture
def sample_listing_data() -> dict:
    """Sample listing data for testing."""
    return {
        "listing_id": "test-listing-001",
        "title": "Beautiful 2BR Apartment in Paris 11th",
        "description": "Spacious apartment with balcony, close to metro.",
        "price": 1200.0,
        "city": "Paris",
        "bedrooms": 2,
        "area_sqm": 55.0,
        "latitude": 48.8566,
        "longitude": 2.3522,
    }


@pytest.fixture
def sample_tenant_profile() -> dict:
    """Sample tenant profile for testing."""
    return {
        "tenant_id": "test-tenant-001",
        "max_budget": 1500.0,
        "preferred_city": "Paris",
        "min_bedrooms": 1,
        "max_commute_minutes": 30,
        "noise_tolerance": 5,
        "has_pets": False,
    }


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate a simple synthetic test image as JPEG bytes."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    buffer = io.BytesIO()
    img.save(buffer, "JPEG", quality=95)
    return buffer.getvalue()


@pytest.fixture
def test_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    """Config with test values -- no real API keys needed."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-for-testing")
    monkeypatch.setenv("GRPC_PORT", "50099")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    return Config.from_env()
