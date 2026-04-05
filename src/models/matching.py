"""Tenant-listing matching algorithms."""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class TenantProfile:
    max_commute_minutes: int = 45
    noise_tolerance: int = 5  # 1-10 scale
    desired_amenities: list[str] = field(default_factory=list)
    social_preference: int = 5  # 1-10 (1=quiet, 10=social)
    min_budget: float = 0
    max_budget: float = float("inf")
    has_pets: bool = False
    pet_type: str | None = None


@dataclass
class ListingProfile:
    listing_id: str = ""
    estimated_commute: int = 30  # minutes
    noise_level: int = 5  # 1-10
    amenities: list[str] = field(default_factory=list)
    social_score: int = 5  # 1-10
    price: float = 0
    pets_allowed: bool = False
    allowed_pet_types: list[str] = field(default_factory=list)


@dataclass
class MatchResult:
    overall_score: float
    commute_score: float
    noise_score: float
    amenity_score: float
    social_score: float
    budget_score: float
    pet_score: float
    narrative: str = ""


class LifestyleMatcher:
    """Multi-criteria tenant-listing matching."""

    def __init__(
        self,
        commute_weight: float = 0.20,
        noise_weight: float = 0.10,
        amenity_weight: float = 0.20,
        social_weight: float = 0.10,
        budget_weight: float = 0.30,
        pet_weight: float = 0.10,
    ):
        self.weights = {
            "commute": commute_weight,
            "noise": noise_weight,
            "amenity": amenity_weight,
            "social": social_weight,
            "budget": budget_weight,
            "pet": pet_weight,
        }

    def compute_commute_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        if tenant.max_commute_minutes <= 0:
            return 1.0
        ratio = listing.estimated_commute / tenant.max_commute_minutes
        return max(0.0, 1.0 - ratio)

    def compute_noise_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        diff = abs(tenant.noise_tolerance - listing.noise_level)
        return max(0.0, 1.0 - diff / 10.0)

    def compute_amenity_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        if not tenant.desired_amenities:
            return 1.0
        desired = set(a.lower() for a in tenant.desired_amenities)
        available = set(a.lower() for a in listing.amenities)
        overlap = desired & available
        return len(overlap) / len(desired)

    def compute_social_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        diff = abs(tenant.social_preference - listing.social_score)
        return max(0.0, 1.0 - diff / 10.0)

    def compute_budget_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        if listing.price <= tenant.max_budget:
            if tenant.min_budget > 0:
                range_size = tenant.max_budget - tenant.min_budget
                if range_size > 0:
                    position = (listing.price - tenant.min_budget) / range_size
                    return 1.0 - abs(position - 0.5) * 0.4
            return 1.0
        overage = (listing.price - tenant.max_budget) / tenant.max_budget
        return max(0.0, 1.0 - overage * 2)

    def compute_pet_score(self, tenant: TenantProfile, listing: ListingProfile) -> float:
        if not tenant.has_pets:
            return 1.0
        if not listing.pets_allowed:
            return 0.0
        if tenant.pet_type and listing.allowed_pet_types:
            if tenant.pet_type.lower() in [p.lower() for p in listing.allowed_pet_types]:
                return 1.0
            return 0.3
        return 1.0

    def match(self, tenant: TenantProfile, listing: ListingProfile) -> MatchResult:
        scores = {
            "commute": self.compute_commute_score(tenant, listing),
            "noise": self.compute_noise_score(tenant, listing),
            "amenity": self.compute_amenity_score(tenant, listing),
            "social": self.compute_social_score(tenant, listing),
            "budget": self.compute_budget_score(tenant, listing),
            "pet": self.compute_pet_score(tenant, listing),
        }

        overall = sum(scores[k] * self.weights[k] for k in scores)

        return MatchResult(
            overall_score=overall,
            commute_score=scores["commute"],
            noise_score=scores["noise"],
            amenity_score=scores["amenity"],
            social_score=scores["social"],
            budget_score=scores["budget"],
            pet_score=scores["pet"],
        )

    def match_properties(
        self,
        tenant: TenantProfile,
        candidates: list[ListingProfile],
        top_n: int = 10,
    ) -> list[MatchResult]:
        results = [self.match(tenant, listing) for listing in candidates]
        results.sort(key=lambda r: r.overall_score, reverse=True)
        return results[:top_n]


class CollaborativeFilter:
    """Collaborative filtering for tenant-listing recommendations."""

    def __init__(
        self,
        content_weight: float = 0.6,
        collaborative_weight: float = 0.4,
    ):
        self.content_weight = content_weight
        self.collaborative_weight = collaborative_weight

    def build_interaction_matrix(
        self, interactions: list[dict], tenant_ids: list[str], listing_ids: list[str]
    ) -> np.ndarray:
        """Build tenant x listing interaction matrix.

        interactions: [{"tenant_id": ..., "listing_id": ..., "score": ...}]
        """
        tenant_idx = {tid: i for i, tid in enumerate(tenant_ids)}
        listing_idx = {lid: i for i, lid in enumerate(listing_ids)}
        matrix = np.zeros((len(tenant_ids), len(listing_ids)))

        for interaction in interactions:
            t_idx = tenant_idx.get(interaction["tenant_id"])
            l_idx = listing_idx.get(interaction["listing_id"])
            if t_idx is not None and l_idx is not None:
                matrix[t_idx, l_idx] = interaction.get("score", 1.0)

        return matrix

    def find_similar_tenants(
        self, target_idx: int, matrix: np.ndarray, top_k: int = 5
    ) -> list[tuple[int, float]]:
        """Find top-K similar tenants by cosine similarity."""
        target_vec = matrix[target_idx]
        target_norm = np.linalg.norm(target_vec)
        if target_norm == 0:
            return []

        similarities: list[tuple[int, float]] = []
        for i in range(matrix.shape[0]):
            if i == target_idx:
                continue
            other_vec = matrix[i]
            other_norm = np.linalg.norm(other_vec)
            if other_norm == 0:
                continue
            cos_sim = float(np.dot(target_vec, other_vec) / (target_norm * other_norm))
            if cos_sim > 0:
                similarities.append((i, cos_sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def _collaborative_scores(
        self,
        target_idx: int,
        matrix: np.ndarray,
        listing_ids: list[str],
    ) -> dict[str, float]:
        """Compute collaborative recommendation scores."""
        similar = self.find_similar_tenants(target_idx, matrix)
        if not similar:
            return {}

        scores: dict[str, float] = {}
        weight_sum = sum(sim for _, sim in similar)

        for listing_j in range(matrix.shape[1]):
            if matrix[target_idx, listing_j] > 0:
                continue  # Skip already-interacted listings
            weighted = sum(
                matrix[i, listing_j] * sim for i, sim in similar
            )
            if weighted > 0 and weight_sum > 0:
                scores[listing_ids[listing_j]] = weighted / weight_sum

        return scores

    def recommend(
        self,
        target_tenant_id: str,
        interactions: list[dict],
        candidates: list[ListingProfile],
        tenant: TenantProfile,
        matcher: LifestyleMatcher,
        top_n: int = 10,
    ) -> list[MatchResult]:
        """Blend collaborative and content-based recommendations."""
        # Content-based scores for all candidates
        content_results = [
            (c, matcher.match(tenant, c)) for c in candidates
        ]

        # Check if we have interaction history
        tenant_ids_set: set[str] = set()
        listing_ids_set: set[str] = set()
        has_target = False
        for interaction in interactions:
            tenant_ids_set.add(interaction["tenant_id"])
            listing_ids_set.add(interaction["listing_id"])
            if interaction["tenant_id"] == target_tenant_id:
                has_target = True

        # Cold start: pure content-based
        if not has_target or not interactions:
            results = [r for _, r in content_results]
            results.sort(key=lambda r: r.overall_score, reverse=True)
            return results[:top_n]

        # Build matrix and get collaborative scores
        tenant_ids = sorted(tenant_ids_set)
        listing_ids = sorted(listing_ids_set)
        matrix = self.build_interaction_matrix(
            interactions, tenant_ids, listing_ids
        )
        target_idx = tenant_ids.index(target_tenant_id)
        collab_scores = self._collaborative_scores(
            target_idx, matrix, listing_ids
        )

        # Blend scores
        blended: list[MatchResult] = []
        for candidate, content_result in content_results:
            collab = collab_scores.get(getattr(candidate, "listing_id", ""), 0.0)
            if collab > 0:
                overall = (
                    self.content_weight * content_result.overall_score
                    + self.collaborative_weight * collab
                )
            else:
                overall = content_result.overall_score

            blended.append(
                MatchResult(
                    overall_score=overall,
                    commute_score=content_result.commute_score,
                    noise_score=content_result.noise_score,
                    amenity_score=content_result.amenity_score,
                    social_score=content_result.social_score,
                    budget_score=content_result.budget_score,
                    pet_score=content_result.pet_score,
                )
            )

        blended.sort(key=lambda r: r.overall_score, reverse=True)
        return blended[:top_n]
