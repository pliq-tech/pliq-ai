"""Unit tests for fraud detection models."""

import io

import numpy as np
from PIL import Image

from src.models.fraud_detection import (
    ELAAnalyzer,
    ELAResult,
    EXIFAnalyzer,
    EXIFResult,
    FFTAnalyzer,
    FFTResult,
    FraudScoreAggregator,
    PriceAnomalyDetector,
)


def _make_image_bytes(
    width: int = 100,
    height: int = 100,
    color: tuple[int, int, int] = (128, 128, 128),
    fmt: str = "JPEG",
) -> bytes:
    """Create synthetic image bytes for testing."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, fmt)
    return buf.getvalue()


def _make_noisy_image_bytes(width: int = 100, height: int = 100) -> bytes:
    """Create a noisy image to trigger higher ELA variance."""
    arr = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=50)
    return buf.getvalue()


class TestELAAnalyzer:
    """Tests for Error Level Analysis."""

    def test_uniform_image_low_score(self) -> None:
        """A uniform solid-color image should have low ELA score."""
        analyzer = ELAAnalyzer()
        image_bytes = _make_image_bytes(color=(128, 128, 128))
        result = analyzer.analyze(image_bytes)
        assert result.score < 0.3
        assert result.heatmap_bytes is not None

    def test_noisy_image_higher_score(self) -> None:
        """A noisy image resaved at low quality should show higher variance."""
        analyzer = ELAAnalyzer()
        image_bytes = _make_noisy_image_bytes()
        result = analyzer.analyze(image_bytes)
        assert result.score >= 0.0
        assert result.heatmap_bytes is not None

    def test_invalid_image_returns_zero(self) -> None:
        """Invalid image bytes should return score 0 with error details."""
        analyzer = ELAAnalyzer()
        result = analyzer.analyze(b"not an image")
        assert result.score == 0.0
        assert "Failed" in result.details

    def test_png_input_is_handled(self) -> None:
        """PNG images should be converted and analyzed without error."""
        analyzer = ELAAnalyzer()
        image_bytes = _make_image_bytes(fmt="PNG")
        result = analyzer.analyze(image_bytes)
        assert result.score >= 0.0
        assert result.heatmap_bytes is not None


class TestFFTAnalyzer:
    """Tests for FFT-based pattern detection."""

    def test_uniform_image_low_score(self) -> None:
        """A uniform image should have few or no frequency peaks."""
        analyzer = FFTAnalyzer()
        image_bytes = _make_image_bytes(color=(128, 128, 128))
        result = analyzer.analyze(image_bytes)
        assert result.score < 0.5

    def test_patterned_image_detects_peaks(self) -> None:
        """An image with repeating patterns should produce peaks."""
        analyzer = FFTAnalyzer()
        # Create a striped pattern
        arr = np.zeros((100, 100), dtype=np.uint8)
        for i in range(100):
            if i % 5 == 0:
                arr[i, :] = 255
        img = Image.fromarray(arr, "L")
        buf = io.BytesIO()
        img.save(buf, "PNG")
        result = analyzer.analyze(buf.getvalue())
        assert result.score >= 0.0
        assert isinstance(result.detected_patterns, list)

    def test_invalid_image_returns_zero(self) -> None:
        """Invalid image bytes should return score 0."""
        analyzer = FFTAnalyzer()
        result = analyzer.analyze(b"corrupted data")
        assert result.score == 0.0


class TestEXIFAnalyzer:
    """Tests for EXIF metadata analysis."""

    def test_jpeg_without_exif_flags_anomaly(self) -> None:
        """A JPEG with no EXIF data should be flagged as suspicious."""
        analyzer = EXIFAnalyzer()
        image_bytes = _make_image_bytes(fmt="JPEG")
        result = analyzer.analyze(image_bytes)
        assert result.score == 0.3
        assert any("Missing EXIF" in a for a in result.anomalies)

    def test_png_without_exif_no_flag(self) -> None:
        """A PNG with no EXIF should not be penalized (PNGs rarely have EXIF)."""
        analyzer = EXIFAnalyzer()
        image_bytes = _make_image_bytes(fmt="PNG")
        result = analyzer.analyze(image_bytes)
        assert result.score == 0.0

    def test_invalid_image_returns_zero(self) -> None:
        """Invalid image bytes should return score 0."""
        analyzer = EXIFAnalyzer()
        result = analyzer.analyze(b"not an image")
        assert result.score == 0.0


class TestFraudScoreAggregator:
    """Tests for the fraud score aggregation logic."""

    def test_aggregate_all_clean_scores(self) -> None:
        """All clean scores should produce a low overall score."""
        aggregator = FraudScoreAggregator()
        report = aggregator.aggregate(
            ela=ELAResult(score=0.1, details="clean"),
            fft=FFTResult(score=0.1, details="clean"),
            exif=EXIFResult(score=0.1, details="clean"),
            reverse_score=0.1,
        )
        assert report.overall_score < 0.3

    def test_aggregate_all_suspicious_scores(self) -> None:
        """All suspicious scores should produce a high overall score."""
        aggregator = FraudScoreAggregator()
        report = aggregator.aggregate(
            ela=ELAResult(score=0.9, details="suspicious"),
            fft=FFTResult(score=0.9, details="suspicious"),
            exif=EXIFResult(score=0.9, details="suspicious"),
            reverse_score=0.9,
        )
        assert report.overall_score > 0.7

    def test_aggregate_with_none_results(self) -> None:
        """Missing results should be treated as score 0."""
        aggregator = FraudScoreAggregator()
        report = aggregator.aggregate(
            ela=None,
            fft=None,
            exif=None,
            reverse_score=0.0,
        )
        assert report.overall_score == 0.0


class TestPriceAnomalyDetector:
    """Tests for price anomaly detection."""

    def test_normal_price_low_score(self) -> None:
        """A price near the median should have a low anomaly score."""
        detector = PriceAnomalyDetector()
        comparable_prices = [1000.0, 1100.0, 1200.0, 1050.0, 1150.0]
        report = detector.detect(listing_price=1100.0, comparable_prices=comparable_prices)
        assert report.score < 0.5

    def test_extremely_low_price_high_score(self) -> None:
        """A price far below comparable listings should have a high score."""
        detector = PriceAnomalyDetector()
        comparable_prices = [1000.0, 1100.0, 1200.0, 1050.0, 1150.0]
        report = detector.detect(listing_price=100.0, comparable_prices=comparable_prices)
        assert report.score > 0.3

    def test_no_comparables_returns_zero(self) -> None:
        """No comparable listings should return zero score with zero confidence."""
        detector = PriceAnomalyDetector()
        report = detector.detect(listing_price=1000.0, comparable_prices=[])
        assert report.score == 0.0
        assert report.confidence == 0.0

    def test_confidence_scales_with_count(self) -> None:
        """Confidence should increase with more comparables."""
        detector = PriceAnomalyDetector()
        few = detector.detect(listing_price=500.0, comparable_prices=[1000.0, 1100.0])
        many = detector.detect(
            listing_price=500.0,
            comparable_prices=[1000.0, 1100.0, 1200.0, 1050.0, 1150.0,
                             1000.0, 1100.0, 1200.0, 1050.0, 1150.0],
        )
        assert many.confidence > few.confidence
