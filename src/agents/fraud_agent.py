"""Fraud detection agent using Google ADK for orchestration."""

import asyncio
import logging

from google.adk import Agent

from src.models.fraud_detection import (
    ELAAnalyzer,
    EXIFAnalyzer,
    FFTAnalyzer,
    FraudScoreAggregator,
    PriceAnomalyDetector,
)

logger = logging.getLogger(__name__)

# Default model for complex reasoning (overridden at runtime via config)
_DEFAULT_PRO_MODEL = "gemini-2.5-pro-preview-05-06"


def analyze_image_tool(image_bytes: bytes, image_format: str = "jpeg") -> dict:
    """Analyze an image for manipulation using ELA, FFT, and EXIF analysis.

    Args:
        image_bytes: Raw image bytes to analyze.
        image_format: Image format identifier (e.g. "jpeg", "png").

    Returns:
        Dictionary with overall fraud score and per-analyzer scores.
    """
    ela = ELAAnalyzer()
    fft = FFTAnalyzer()
    exif = EXIFAnalyzer()

    ela_result = ela.analyze(image_bytes)
    fft_result = fft.analyze(image_bytes)
    exif_result = exif.analyze(image_bytes)

    aggregator = FraudScoreAggregator()
    report = aggregator.aggregate(
        ela=ela_result,
        fft=fft_result,
        exif=exif_result,
    )

    return {
        "overall_score": report.overall_score,
        "ela_score": ela_result.score,
        "ela_details": ela_result.details,
        "fft_score": fft_result.score,
        "fft_patterns": fft_result.detected_patterns,
        "fft_details": fft_result.details,
        "exif_score": exif_result.score,
        "exif_anomalies": exif_result.anomalies,
        "exif_details": exif_result.details,
    }


def check_price_anomaly_tool(
    listing_price: float,
    comparable_prices: list[float],
) -> dict:
    """Check if a listing price is anomalous compared to comparable listings.

    Args:
        listing_price: The price of the listing under evaluation.
        comparable_prices: Prices of comparable listings in the area.

    Returns:
        Dictionary with anomaly score, z-score, confidence, and explanation.
    """
    detector = PriceAnomalyDetector()
    report = detector.detect(listing_price, comparable_prices)
    return {
        "anomaly_score": report.score,
        "confidence": report.confidence,
        "z_score": report.z_score,
        "median_price": report.median_price,
        "comparable_count": report.comparable_count,
        "explanation": report.explanation,
    }


def check_duplication_tool(
    listing_id: str,
    title: str,
    description: str,
    image_phashes: list[str] | None = None,
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict:
    """Check if a listing is a potential duplicate of existing listings.

    Args:
        listing_id: Unique identifier for the listing.
        title: Listing title text.
        description: Listing description text.
        image_phashes: Perceptual hashes of listing images.
        latitude: Listing latitude coordinate.
        longitude: Listing longitude coordinate.

    Returns:
        Dictionary with duplication scores and matched listing IDs.
    """
    # Placeholder: full implementation requires embedding service and
    # backend database lookup via gRPC. Returns zero scores until
    # the infrastructure layer is connected.
    logger.info(
        "Duplication check requested for listing_id=%s", listing_id
    )
    return {
        "duplication_score": 0.0,
        "text_similarity": 0.0,
        "image_similarity": 0.0,
        "location_proximity": 0.0,
        "matched_listing_ids": [],
        "summary": "Duplication detection pending infrastructure integration",
    }


def create_fraud_agent(model: str | None = None) -> Agent:
    """Create the fraud detection ADK agent.

    Args:
        model: Gemini model identifier. Defaults to pro model for
               complex fraud reasoning tasks.

    Returns:
        Configured Google ADK Agent instance.
    """
    return Agent(
        name="fraud_detector",
        model=model or _DEFAULT_PRO_MODEL,
        description="Analyzes listing images and data for fraud indicators",
        instructions=(
            "You are a fraud detection specialist for rental listings. "
            "You analyze images for manipulation, prices for anomalies, "
            "and listings for duplication. "
            "Always provide confidence scores and human-readable explanations. "
            "When multiple signals indicate fraud, explain how they correlate."
        ),
        tools=[
            analyze_image_tool,
            check_price_anomaly_tool,
            check_duplication_tool,
        ],
    )


# Module-level agent instance with default model
fraud_agent = create_fraud_agent()


async def run_sequential_fraud_check(
    image_bytes: bytes,
    listing_data: dict,
    fraud_threshold: float = 0.3,
) -> dict:
    """Sequential workflow: image analysis -> price check -> duplication.

    Stops early if the image fraud score exceeds the threshold,
    skipping price and duplication checks.

    Args:
        image_bytes: Raw image bytes to analyze.
        listing_data: Dict with keys: listing_price, comparable_prices,
                      listing_id, title, description, image_phashes,
                      latitude, longitude.
        fraud_threshold: Image score above which to skip further checks.

    Returns:
        Combined fraud check results dictionary.
    """
    logger.info("Starting sequential fraud check")

    image_result = analyze_image_tool(image_bytes)
    combined = {"image": image_result}

    if image_result["overall_score"] >= fraud_threshold:
        logger.warning(
            "Image fraud score %.2f exceeds threshold %.2f, skipping remaining checks",
            image_result["overall_score"],
            fraud_threshold,
        )
        combined["skipped"] = ["price_anomaly", "duplication"]
        return combined

    price_result = check_price_anomaly_tool(
        listing_price=listing_data.get("listing_price", 0.0),
        comparable_prices=listing_data.get("comparable_prices", []),
    )
    combined["price"] = price_result

    duplication_result = check_duplication_tool(
        listing_id=listing_data.get("listing_id", ""),
        title=listing_data.get("title", ""),
        description=listing_data.get("description", ""),
        image_phashes=listing_data.get("image_phashes"),
        latitude=listing_data.get("latitude", 0.0),
        longitude=listing_data.get("longitude", 0.0),
    )
    combined["duplication"] = duplication_result

    return combined


async def run_parallel_fraud_check(
    image_bytes: bytes,
    listing_data: dict,
) -> dict:
    """Parallel workflow: all fraud checks run concurrently.

    Args:
        image_bytes: Raw image bytes to analyze.
        listing_data: Dict with keys: listing_price, comparable_prices,
                      listing_id, title, description, image_phashes,
                      latitude, longitude.

    Returns:
        Combined fraud check results dictionary.
    """
    logger.info("Starting parallel fraud check")

    loop = asyncio.get_running_loop()

    image_task = loop.run_in_executor(None, analyze_image_tool, image_bytes)
    price_task = loop.run_in_executor(
        None,
        check_price_anomaly_tool,
        listing_data.get("listing_price", 0.0),
        listing_data.get("comparable_prices", []),
    )
    duplication_task = loop.run_in_executor(
        None,
        check_duplication_tool,
        listing_data.get("listing_id", ""),
        listing_data.get("title", ""),
        listing_data.get("description", ""),
        listing_data.get("image_phashes"),
        listing_data.get("latitude", 0.0),
        listing_data.get("longitude", 0.0),
    )

    image_result, price_result, duplication_result = await asyncio.gather(
        image_task, price_task, duplication_task
    )

    return {
        "image": image_result,
        "price": price_result,
        "duplication": duplication_result,
    }
