"""Lifestyle matching agent using Google ADK for compatibility scoring."""

import logging

from google.adk import Agent

from src.models.matching import LifestyleMatcher, ListingProfile, TenantProfile

logger = logging.getLogger(__name__)

# Default model for fast scoring and narrative generation
_DEFAULT_FLASH_MODEL = "gemini-2.5-flash-preview-05-20"


def _build_tenant_profile(tenant_data: dict) -> TenantProfile:
    """Convert a raw dict into a TenantProfile dataclass.

    Args:
        tenant_data: Dict with tenant preference fields.

    Returns:
        Populated TenantProfile instance.
    """
    return TenantProfile(
        max_commute_minutes=tenant_data.get("max_commute_minutes", 45),
        noise_tolerance=tenant_data.get("noise_tolerance", 5),
        desired_amenities=tenant_data.get("desired_amenities", []),
        social_preference=tenant_data.get("social_preference", 5),
        min_budget=tenant_data.get("min_budget", 0),
        max_budget=tenant_data.get("max_budget", float("inf")),
        has_pets=tenant_data.get("has_pets", False),
        pet_type=tenant_data.get("pet_type"),
    )


def _build_listing_profile(listing_data: dict) -> ListingProfile:
    """Convert a raw dict into a ListingProfile dataclass.

    Args:
        listing_data: Dict with listing attribute fields.

    Returns:
        Populated ListingProfile instance.
    """
    return ListingProfile(
        estimated_commute=listing_data.get("estimated_commute", 30),
        noise_level=listing_data.get("noise_level", 5),
        amenities=listing_data.get("amenities", []),
        social_score=listing_data.get("social_score", 5),
        price=listing_data.get("price", 0),
        pets_allowed=listing_data.get("pets_allowed", False),
        allowed_pet_types=listing_data.get("allowed_pet_types", []),
    )


def compute_commute_tool(tenant_data: dict, listing_data: dict) -> dict:
    """Compute commute compatibility between tenant and listing.

    Args:
        tenant_data: Dict with tenant profile fields.
        listing_data: Dict with listing profile fields.

    Returns:
        Dictionary with commute_score (0.0 to 1.0) and details.
    """
    tenant = _build_tenant_profile(tenant_data)
    listing = _build_listing_profile(listing_data)
    matcher = LifestyleMatcher()
    score = matcher.compute_commute_score(tenant, listing)
    return {
        "commute_score": score,
        "max_commute_minutes": tenant.max_commute_minutes,
        "estimated_commute": listing.estimated_commute,
    }


def compute_noise_match_tool(tenant_data: dict, listing_data: dict) -> dict:
    """Compute noise level compatibility between tenant and listing.

    Args:
        tenant_data: Dict with tenant profile fields.
        listing_data: Dict with listing profile fields.

    Returns:
        Dictionary with noise_score (0.0 to 1.0) and details.
    """
    tenant = _build_tenant_profile(tenant_data)
    listing = _build_listing_profile(listing_data)
    matcher = LifestyleMatcher()
    score = matcher.compute_noise_score(tenant, listing)
    return {
        "noise_score": score,
        "tenant_tolerance": tenant.noise_tolerance,
        "listing_noise_level": listing.noise_level,
    }


def compute_amenity_overlap_tool(
    tenant_data: dict,
    listing_data: dict,
) -> dict:
    """Compute amenity overlap between tenant desires and listing offers.

    Args:
        tenant_data: Dict with tenant profile fields (desired_amenities).
        listing_data: Dict with listing profile fields (amenities).

    Returns:
        Dictionary with amenity_score (0.0 to 1.0), matched and missing lists.
    """
    tenant = _build_tenant_profile(tenant_data)
    listing = _build_listing_profile(listing_data)
    matcher = LifestyleMatcher()
    score = matcher.compute_amenity_score(tenant, listing)

    desired = set(a.lower() for a in tenant.desired_amenities)
    available = set(a.lower() for a in listing.amenities)
    matched = sorted(desired & available)
    missing = sorted(desired - available)

    return {
        "amenity_score": score,
        "matched_amenities": matched,
        "missing_amenities": missing,
    }


def compute_full_match_tool(tenant_data: dict, listing_data: dict) -> dict:
    """Compute the full lifestyle match between a tenant and listing.

    Uses all scoring dimensions: commute, noise, amenity, social,
    budget, and pet compatibility.

    Args:
        tenant_data: Dict with tenant profile fields.
        listing_data: Dict with listing profile fields.

    Returns:
        Dictionary with overall_score and per-dimension scores.
    """
    tenant = _build_tenant_profile(tenant_data)
    listing = _build_listing_profile(listing_data)
    matcher = LifestyleMatcher()
    result = matcher.match(tenant, listing)

    return {
        "overall_score": result.overall_score,
        "commute_score": result.commute_score,
        "noise_score": result.noise_score,
        "amenity_score": result.amenity_score,
        "social_score": result.social_score,
        "budget_score": result.budget_score,
        "pet_score": result.pet_score,
    }


def generate_narrative_tool(
    match_scores: dict,
    tenant_data: dict,
    listing_data: dict,
) -> str:
    """Generate a personalized narrative explaining a match.

    In production this is powered by Gemini Flash for natural language.
    Currently returns a template-based narrative as a placeholder.

    Args:
        match_scores: Dict with per-dimension scores from compute_full_match_tool.
        tenant_data: Dict with tenant profile fields.
        listing_data: Dict with listing profile fields.

    Returns:
        Human-readable narrative string explaining the match.
    """
    overall = match_scores.get("overall_score", 0.0)
    strengths = []
    weaknesses = []

    dimension_labels = {
        "commute_score": "commute",
        "noise_score": "noise level",
        "amenity_score": "amenities",
        "social_score": "social environment",
        "budget_score": "budget fit",
        "pet_score": "pet policy",
    }

    for key, label in dimension_labels.items():
        score = match_scores.get(key, 0.0)
        if score >= 0.8:
            strengths.append(label)
        elif score < 0.5:
            weaknesses.append(label)

    parts = [f"Overall compatibility: {overall:.0%}."]
    if strengths:
        parts.append(f"Strong fit for: {', '.join(strengths)}.")
    if weaknesses:
        parts.append(f"Potential concerns: {', '.join(weaknesses)}.")

    return " ".join(parts)


def create_matching_agent(model: str | None = None) -> Agent:
    """Create the lifestyle matching ADK agent.

    Args:
        model: Gemini model identifier. Defaults to flash model for
               fast scoring and narrative generation.

    Returns:
        Configured Google ADK Agent instance.
    """
    return Agent(
        name="lifestyle_matcher",
        model=model or _DEFAULT_FLASH_MODEL,
        description=(
            "Computes lifestyle compatibility between tenants and listings"
        ),
        instructions=(
            "You are a lifestyle compatibility analyst. "
            "Given a tenant profile and listing attributes, compute how well "
            "they match. Consider commute, noise, pets, amenities, social "
            "environment, and budget. "
            "Use compute_full_match_tool for complete scoring, or individual "
            "tools for targeted analysis. "
            "Always call generate_narrative_tool at the end to provide a "
            "personalized explanation."
        ),
        tools=[
            compute_commute_tool,
            compute_noise_match_tool,
            compute_amenity_overlap_tool,
            compute_full_match_tool,
            generate_narrative_tool,
        ],
    )


# Module-level agent instance with default model
matching_agent = create_matching_agent()
