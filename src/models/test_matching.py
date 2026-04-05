"""Unit tests for matching models."""

from src.models.matching import LifestyleMatcher, ListingProfile, TenantProfile


class TestLifestyleMatcher:
    """Tests for the lifestyle matcher."""

    def test_perfect_match_scores_high(self) -> None:
        """A listing that matches tenant preferences well should score high."""
        matcher = LifestyleMatcher()
        tenant = TenantProfile(
            max_commute_minutes=30,
            noise_tolerance=5,
            desired_amenities=["gym", "parking"],
            social_preference=5,
            max_budget=1500.0,
            has_pets=False,
        )
        listing = ListingProfile(
            estimated_commute=15,
            noise_level=5,
            amenities=["gym", "parking", "pool"],
            social_score=5,
            price=1200.0,
            pets_allowed=False,
        )
        result = matcher.match(tenant, listing)
        assert result.overall_score >= 0.7

    def test_over_budget_scores_low_budget(self) -> None:
        """A listing over budget should have a low budget score."""
        matcher = LifestyleMatcher()
        tenant = TenantProfile(
            max_commute_minutes=30,
            noise_tolerance=5,
            desired_amenities=[],
            social_preference=5,
            max_budget=800.0,
            has_pets=False,
        )
        listing = ListingProfile(
            estimated_commute=15,
            noise_level=5,
            amenities=[],
            social_score=5,
            price=2000.0,
            pets_allowed=False,
        )
        result = matcher.match(tenant, listing)
        assert result.budget_score < 0.3

    def test_pet_mismatch_penalized(self) -> None:
        """A tenant with pets and a no-pets listing should get pet_score 0."""
        matcher = LifestyleMatcher()
        tenant = TenantProfile(has_pets=True, pet_type="dog", max_budget=2000.0)
        listing = ListingProfile(price=1000.0, pets_allowed=False)
        result = matcher.match(tenant, listing)
        assert result.pet_score == 0.0

    def test_match_properties_returns_sorted(self) -> None:
        """match_properties should return results sorted by overall_score descending."""
        matcher = LifestyleMatcher()
        tenant = TenantProfile(max_budget=1500.0)
        candidates = [
            ListingProfile(price=3000.0),  # Over budget
            ListingProfile(price=1200.0),  # Within budget
            ListingProfile(price=1000.0),  # Within budget
        ]
        results = matcher.match_properties(tenant, candidates, top_n=2)
        assert len(results) == 2
        assert results[0].overall_score >= results[1].overall_score
