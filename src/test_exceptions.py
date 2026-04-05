"""Unit tests for src.exceptions exception hierarchy."""

from src.exceptions import (
    AgentExecutionError,
    ConfigError,
    FraudDetectionError,
    ImageForensicsError,
    LeaseAnalysisError,
    MatchingError,
    PliqAIError,
    PriceAnomalyError,
    SearchError,
)


def test_base_error_with_request_id() -> None:
    """PliqAIError stores request_id when provided."""
    # Arrange & Act
    error = PliqAIError("something failed", request_id="req-123")

    # Assert
    assert str(error) == "something failed"
    assert error.request_id == "req-123"


def test_base_error_without_request_id() -> None:
    """PliqAIError defaults request_id to None when not provided."""
    # Arrange & Act
    error = PliqAIError("something failed")

    # Assert
    assert str(error) == "something failed"
    assert error.request_id is None


def test_hierarchy_fraud_detection() -> None:
    """FraudDetectionError is a PliqAIError."""
    # Arrange & Act
    error = FraudDetectionError("fraud error")

    # Assert
    assert isinstance(error, PliqAIError)
    assert isinstance(error, Exception)


def test_hierarchy_image_forensics() -> None:
    """ImageForensicsError is both a FraudDetectionError and a PliqAIError."""
    # Arrange & Act
    error = ImageForensicsError("image error", request_id="req-456")

    # Assert
    assert isinstance(error, FraudDetectionError)
    assert isinstance(error, PliqAIError)
    assert error.request_id == "req-456"


def test_hierarchy_price_anomaly() -> None:
    """PriceAnomalyError is both a FraudDetectionError and a PliqAIError."""
    # Arrange & Act
    error = PriceAnomalyError("price error")

    # Assert
    assert isinstance(error, FraudDetectionError)
    assert isinstance(error, PliqAIError)


def test_hierarchy_other_errors() -> None:
    """All domain errors inherit from PliqAIError."""
    # Arrange & Act & Assert
    assert isinstance(ConfigError("c"), PliqAIError)
    assert isinstance(MatchingError("m"), PliqAIError)
    assert isinstance(LeaseAnalysisError("l"), PliqAIError)
    assert isinstance(SearchError("s"), PliqAIError)
    assert isinstance(AgentExecutionError("a"), PliqAIError)


def test_error_message_preserved() -> None:
    """Custom message is preserved through the exception hierarchy."""
    # Arrange
    message = "detailed error description"

    # Act
    errors = [
        PliqAIError(message),
        ConfigError(message),
        FraudDetectionError(message),
        ImageForensicsError(message),
        PriceAnomalyError(message),
        MatchingError(message),
        LeaseAnalysisError(message),
        SearchError(message),
        AgentExecutionError(message),
    ]

    # Assert
    for error in errors:
        assert str(error) == message


def test_fraud_detection_error_not_caught_as_matching() -> None:
    """FraudDetectionError is not a MatchingError (sibling branches)."""
    # Arrange & Act
    error = FraudDetectionError("fraud")

    # Assert
    assert not isinstance(error, MatchingError)
    assert not isinstance(error, LeaseAnalysisError)
    assert not isinstance(error, SearchError)
