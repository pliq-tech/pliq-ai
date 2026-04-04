"""Tenant-listing matching algorithms."""

from dataclasses import dataclass, field


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
