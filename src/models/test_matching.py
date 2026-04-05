"""Unit tests for matching models."""

from src.models.matching import (
    CollaborativeFilter,
    LifestyleMatcher,
    ListingProfile,
    MatchResult,
    TenantProfile,
)


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


class TestCollaborativeFilter:
    """Tests for collaborative filtering."""

    def test_cold_start_returns_content_based(self) -> None:
        """New tenant with no history should get pure content-based results."""
        cf = CollaborativeFilter()
        matcher = LifestyleMatcher()
        tenant = TenantProfile(max_budget=1500.0)
        candidates = [
            ListingProfile(listing_id="l1", price=1200.0),
            ListingProfile(listing_id="l2", price=1400.0),
        ]
        results = cf.recommend(
            target_tenant_id="new-tenant",
            interactions=[],
            candidates=candidates,
            tenant=tenant,
            matcher=matcher,
            top_n=5,
        )
        assert len(results) == 2
        assert all(isinstance(r, MatchResult) for r in results)

    def test_cold_start_no_target_in_interactions(self) -> None:
        """Target tenant not in interactions should fall back to content-based."""
        cf = CollaborativeFilter()
        matcher = LifestyleMatcher()
        tenant = TenantProfile(max_budget=1500.0)
        candidates = [
            ListingProfile(listing_id="l1", price=1200.0),
            ListingProfile(listing_id="l2", price=1400.0),
        ]
        interactions = [
            {"tenant_id": "other-tenant", "listing_id": "l1", "score": 1.0},
        ]
        results = cf.recommend(
            target_tenant_id="new-tenant",
            interactions=interactions,
            candidates=candidates,
            tenant=tenant,
            matcher=matcher,
            top_n=5,
        )
        assert len(results) == 2

    def test_with_interactions_blends_scores(self) -> None:
        """Tenant with interaction history should blend collaborative and content."""
        cf = CollaborativeFilter(content_weight=0.6, collaborative_weight=0.4)
        matcher = LifestyleMatcher()
        tenant = TenantProfile(max_budget=1500.0)
        candidates = [
            ListingProfile(listing_id="l1", price=1200.0),
            ListingProfile(listing_id="l2", price=1400.0),
            ListingProfile(listing_id="l3", price=1000.0),
        ]
        interactions = [
            {"tenant_id": "t1", "listing_id": "l1", "score": 1.0},
            {"tenant_id": "t1", "listing_id": "l2", "score": 0.8},
            {"tenant_id": "t2", "listing_id": "l1", "score": 0.9},
            {"tenant_id": "t2", "listing_id": "l3", "score": 0.7},
        ]
        results = cf.recommend(
            target_tenant_id="t1",
            interactions=interactions,
            candidates=candidates,
            tenant=tenant,
            matcher=matcher,
            top_n=5,
        )
        assert len(results) == 3
        assert results[0].overall_score >= results[1].overall_score

    def test_find_similar_tenants_returns_ranked(self) -> None:
        """Similar tenants should be returned sorted by similarity."""
        cf = CollaborativeFilter()
        import numpy as np

        matrix = np.array([
            [1.0, 0.8, 0.0],  # target
            [0.9, 0.7, 0.1],  # similar
            [0.0, 0.0, 1.0],  # different
        ])
        similar = cf.find_similar_tenants(target_idx=0, matrix=matrix, top_k=2)
        assert len(similar) >= 1
        assert similar[0][0] == 1  # tenant at index 1 is most similar

    def test_find_similar_tenants_empty_row(self) -> None:
        """Target with no interactions should return empty list."""
        cf = CollaborativeFilter()
        import numpy as np

        matrix = np.array([
            [0.0, 0.0, 0.0],
            [1.0, 0.5, 0.3],
        ])
        similar = cf.find_similar_tenants(target_idx=0, matrix=matrix)
        assert similar == []
