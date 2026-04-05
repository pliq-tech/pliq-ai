"""Unit tests for duplication detection models."""

from src.models.duplication_detection import (
    CandidateListing,
    DuplicateReport,
    DuplicationDetector,
)


class TestDuplicationDetector:
    """Tests for the duplication detection pipeline."""

    def test_text_similarity_identical(self) -> None:
        """Identical text should return similarity of 1.0."""
        detector = DuplicationDetector()
        score = detector.compute_text_similarity(
            "beautiful apartment in Paris", "beautiful apartment in Paris"
        )
        assert score == 1.0

    def test_text_similarity_disjoint(self) -> None:
        """Completely different text should return 0.0."""
        detector = DuplicationDetector()
        score = detector.compute_text_similarity(
            "hello world", "foo bar baz"
        )
        assert score == 0.0

    def test_text_similarity_partial_overlap(self) -> None:
        """Partially overlapping text should return a value between 0 and 1."""
        detector = DuplicationDetector()
        score = detector.compute_text_similarity(
            "beautiful apartment in Paris center",
            "beautiful apartment in Lyon center",
        )
        assert 0.0 < score < 1.0

    def test_text_similarity_empty_returns_zero(self) -> None:
        """Empty string should return 0.0."""
        detector = DuplicationDetector()
        assert detector.compute_text_similarity("", "hello") == 0.0
        assert detector.compute_text_similarity("hello", "") == 0.0

    def test_image_similarity_identical_hash(self) -> None:
        """Identical perceptual hashes should return 1.0."""
        detector = DuplicationDetector()
        score = detector.compute_image_similarity("abcdef01", "abcdef01")
        assert score == 1.0

    def test_image_similarity_different_hash(self) -> None:
        """Very different hashes should return a low score."""
        detector = DuplicationDetector()
        score = detector.compute_image_similarity("00000000", "ffffffff")
        assert score < 0.5

    def test_image_similarity_empty_returns_zero(self) -> None:
        """Empty hash strings should return 0.0."""
        detector = DuplicationDetector()
        assert detector.compute_image_similarity("", "abcdef") == 0.0

    def test_image_similarity_invalid_hex_returns_zero(self) -> None:
        """Non-hex strings should return 0.0."""
        detector = DuplicationDetector()
        assert detector.compute_image_similarity("xyz", "abc") == 0.0

    def test_location_proximity_same_point(self) -> None:
        """Same coordinates should return 1.0."""
        detector = DuplicationDetector()
        score = detector.compute_location_proximity(48.8566, 2.3522, 48.8566, 2.3522)
        assert score == 1.0

    def test_location_proximity_far_away(self) -> None:
        """Locations >5km apart should return 0.0."""
        detector = DuplicationDetector()
        # Paris to Versailles (~17km)
        score = detector.compute_location_proximity(48.8566, 2.3522, 48.8049, 2.1204)
        assert score == 0.0

    def test_location_proximity_intermediate(self) -> None:
        """Locations between 50m and 5km should return a value between 0 and 1."""
        detector = DuplicationDetector()
        # Small offset (~1km)
        score = detector.compute_location_proximity(48.8566, 2.3522, 48.8656, 2.3522)
        assert 0.0 < score < 1.0

    def test_detect_no_candidates_returns_zero(self) -> None:
        """No candidates should produce zero duplication score."""
        detector = DuplicationDetector()
        report = detector.detect(
            title="Test", description="A listing",
            image_phashes=["abc123"], latitude=48.8566, longitude=2.3522,
            candidates=[],
        )
        assert report.duplication_score == 0.0

    def test_detect_identical_listing_near_location(self) -> None:
        """Same text and location should produce a high duplication score."""
        detector = DuplicationDetector()
        candidate = CandidateListing(
            listing_id="dup-1",
            title="Beautiful apartment",
            description="in Paris near metro",
            image_phashes=["abcdef01"],
            latitude=48.8566,
            longitude=2.3522,
        )
        report = detector.detect(
            title="Beautiful apartment",
            description="in Paris near metro",
            image_phashes=["abcdef01"],
            latitude=48.8566,
            longitude=2.3522,
            candidates=[candidate],
        )
        assert report.duplication_score > 0.5
        assert "dup-1" in report.matched_listing_ids

    def test_detect_different_listing_far_location(self) -> None:
        """Different text and far location should produce a low score."""
        detector = DuplicationDetector()
        candidate = CandidateListing(
            listing_id="unique-1",
            title="Cozy studio",
            description="in Lyon old town",
            image_phashes=["00000000"],
            latitude=45.7640,
            longitude=4.8357,
        )
        report = detector.detect(
            title="Modern loft",
            description="in Marseille port area",
            image_phashes=["ffffffff"],
            latitude=43.2965,
            longitude=5.3698,
            candidates=[candidate],
        )
        assert report.duplication_score < 0.3
