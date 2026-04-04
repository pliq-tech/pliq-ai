from typing import Optional


class PliqAIError(Exception):
    """Base exception for all pliq-ai errors."""

    def __init__(self, message: str, request_id: Optional[str] = None):
        super().__init__(message)
        self.request_id = request_id


class ConfigError(PliqAIError):
    """Configuration loading or validation error."""


class FraudDetectionError(PliqAIError):
    """Error during fraud detection analysis."""


class ImageForensicsError(FraudDetectionError):
    """Error during image forensics analysis."""


class PriceAnomalyError(FraudDetectionError):
    """Error during price anomaly detection."""


class MatchingError(PliqAIError):
    """Error during tenant-listing matching."""


class LeaseAnalysisError(PliqAIError):
    """Error during lease clause analysis."""


class SearchError(PliqAIError):
    """Error during property search."""


class AgentExecutionError(PliqAIError):
    """Error during agent orchestration."""
