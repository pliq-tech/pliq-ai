"""Property search agent using Google ADK for natural language queries."""

import logging

from google.adk import Agent

logger = logging.getLogger(__name__)

# Default model for search reasoning
_DEFAULT_PRO_MODEL = "gemini-2.5-pro-preview-05-06"


def search_listings_tool(
    query: str,
    filters: dict | None = None,
) -> dict:
    """Search listings based on a structured query and optional filters.

    In production this calls the backend listing service via internal gRPC.

    Args:
        query: Natural language or structured search query.
        filters: Optional dict with filter keys (city, min_price, max_price,
                 property_type, num_rooms, amenities).

    Returns:
        Dictionary with results list and total count.
    """
    logger.info("Search requested: query=%s, filters=%s", query, filters)
    # Placeholder: production implementation calls pliq-back via gRPC
    return {"results": [], "total": 0, "query": query, "filters": filters or {}}


def filter_by_price_tool(
    min_price: float = 0.0,
    max_price: float = 0.0,
) -> dict:
    """Build a price filter for listing search.

    Args:
        min_price: Minimum monthly rent in EUR.
        max_price: Maximum monthly rent in EUR. Use 0 for no upper limit.

    Returns:
        Dictionary with the price filter parameters.
    """
    effective_max = max_price if max_price > 0 else float("inf")
    return {
        "filter_type": "price",
        "min_price": min_price,
        "max_price": effective_max,
    }


def filter_by_location_tool(
    city: str = "",
    latitude: float = 0.0,
    longitude: float = 0.0,
    radius_km: float = 5.0,
) -> dict:
    """Build a location filter for listing search.

    Args:
        city: City name to search in.
        latitude: Center latitude for radius search.
        longitude: Center longitude for radius search.
        radius_km: Search radius in kilometers.

    Returns:
        Dictionary with the location filter parameters.
    """
    return {
        "filter_type": "location",
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "radius_km": radius_km,
    }


def filter_by_amenities_tool(
    required_amenities: list[str] | None = None,
) -> dict:
    """Build an amenities filter for listing search.

    Args:
        required_amenities: List of amenity names the listing must have
                           (e.g. ["parking", "elevator", "balcony"]).

    Returns:
        Dictionary with the amenities filter parameters.
    """
    return {
        "filter_type": "amenities",
        "required_amenities": required_amenities or [],
    }


def sort_results_tool(
    results: list[dict],
    sort_by: str = "relevance",
) -> list[dict]:
    """Sort search results by a given criterion.

    Args:
        results: List of listing result dictionaries.
        sort_by: Sort criterion: "relevance", "price_asc", "price_desc",
                 "date_newest".

    Returns:
        Sorted list of listing result dictionaries.
    """
    if not results:
        return results

    sort_keys = {
        "price_asc": lambda r: r.get("price", 0),
        "price_desc": lambda r: r.get("price", 0),
        "date_newest": lambda r: r.get("created_at", ""),
    }

    if sort_by in sort_keys:
        reverse = sort_by in ("price_desc", "date_newest")
        return sorted(results, key=sort_keys[sort_by], reverse=reverse)

    # Default: sort by relevance_score descending
    return sorted(
        results,
        key=lambda r: r.get("relevance_score", 0),
        reverse=True,
    )


def create_search_agent(model: str | None = None) -> Agent:
    """Create the property search ADK agent.

    Args:
        model: Gemini model identifier. Defaults to pro model for
               query understanding and search orchestration.

    Returns:
        Configured Google ADK Agent instance.
    """
    return Agent(
        name="property_search",
        model=model or _DEFAULT_PRO_MODEL,
        description="Searches verified rental listings based on tenant criteria",
        instructions=(
            "You are a property search assistant for verified tenants. "
            "Parse natural-language queries into structured filters. "
            "Only return listings the tenant is authorized to see based "
            "on their verification level. "
            "Explain why each result matches the query. "
            "When the query is ambiguous, ask clarifying questions. "
            "Combine multiple filter tools to narrow results before sorting."
        ),
        tools=[
            search_listings_tool,
            filter_by_price_tool,
            filter_by_location_tool,
            filter_by_amenities_tool,
            sort_results_tool,
        ],
    )


# Module-level agent instance with default model
search_agent = create_search_agent()
