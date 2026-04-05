"""Unit tests for fraud detection models."""

from src.models.fraud_detection import (
    ELAResult,
    EXIFResult,
    FFTResult,
    FraudScoreAggregator,
    PriceAnomalyDetector,
)


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
