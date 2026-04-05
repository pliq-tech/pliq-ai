"""Domain protocols (interfaces) for dependency inversion."""

from typing import Protocol

from .models import DocumentResult, FraudResult, MatchResult


class FraudDetector(Protocol):
    """Protocol for fraud detection implementations."""

    async def analyze_listing(
        self,
        listing_id: str,
        title: str,
        description: str,
        price: float,
        images: list[bytes],
    ) -> FraudResult: ...


class TenantMatcher(Protocol):
    """Protocol for tenant-listing matching implementations."""

    async def rank_listings(
        self, tenant_profile: dict, listings: list[dict]
    ) -> list[MatchResult]: ...


class DocumentAnalyzer(Protocol):
    """Protocol for document analysis implementations."""

    async def analyze_document(
        self, document_id: str, document_bytes: bytes, document_type: str
    ) -> DocumentResult: ...
