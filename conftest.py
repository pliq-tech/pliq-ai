"""Root conftest for pliq-ai test suite."""

import pytest


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
