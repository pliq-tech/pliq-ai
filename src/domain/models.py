"""Domain models for AI service results."""

from pydantic import BaseModel, Field


class FraudResult(BaseModel):
    """Result of fraud detection analysis."""
    listing_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    image_score: float = Field(ge=0.0, le=1.0)
    text_score: float = Field(ge=0.0, le=1.0)
    price_score: float = Field(ge=0.0, le=1.0)
    duplicate_score: float = Field(ge=0.0, le=1.0)
    is_fraudulent: bool
    flags: list[str] = Field(default_factory=list)
    explanation: str = ""


class MatchResult(BaseModel):
    """Result of tenant-listing matching."""
    listing_id: str
    overall_score: float = Field(ge=0.0, le=1.0)
    commute_score: float = Field(ge=0.0, le=1.0)
    budget_score: float = Field(ge=0.0, le=1.0)
    amenity_score: float = Field(ge=0.0, le=1.0)
    noise_score: float = Field(ge=0.0, le=1.0)
    social_score: float = Field(ge=0.0, le=1.0)


class DocumentResult(BaseModel):
    """Result of document analysis."""
    document_id: str
    is_valid: bool
    extracted_fields: dict[str, str] = Field(default_factory=dict)
    inconsistencies: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class AgentRequest(BaseModel):
    """Base request model for agent invocations."""
    request_id: str
    agent_type: str


class AgentResponse(BaseModel):
    """Base response model for agent invocations."""
    request_id: str
    success: bool
    error: str | None = None
