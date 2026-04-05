"""gRPC handler for MatchingService."""

import logging

import grpc

from src.config import Config
from src import matching_pb2
from src import matching_pb2_grpc

logger = logging.getLogger(__name__)


class MatchingHandler(matching_pb2_grpc.MatchingServiceServicer):
    """Stub implementation of the MatchingService."""

    def __init__(self, config: Config) -> None:
        self._config = config

    async def MatchProperties(
        self,
        request: matching_pb2.MatchRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.MatchResponse:
        """Match a tenant profile against candidate listings."""
        try:
            if not request.tenant.tenant_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "tenant.tenant_id is required",
                )
            if not request.candidates:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "at least one candidate listing is required",
                )

            logger.info(
                "MatchProperties: tenant_id=%s candidates=%d request_id=%s",
                request.tenant.tenant_id,
                len(request.candidates),
                request.request_id,
            )

            return matching_pb2.MatchResponse(
                request_id=request.request_id,
                results=[],
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("MatchProperties failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def CalculateLifestyleScore(
        self,
        request: matching_pb2.LifestyleScoreRequest,
        context: grpc.aio.ServicerContext,
    ) -> matching_pb2.LifestyleScoreResponse:
        """Calculate a lifestyle compatibility score for a single pair."""
        try:
            if not request.tenant.tenant_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "tenant.tenant_id is required",
                )
            if not request.listing.listing_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "listing.listing_id is required",
                )

            logger.info(
                "CalculateLifestyleScore: tenant=%s listing=%s request_id=%s",
                request.tenant.tenant_id,
                request.listing.listing_id,
                request.request_id,
            )

            return matching_pb2.LifestyleScoreResponse(
                request_id=request.request_id,
                result=matching_pb2.MatchResult(
                    listing_id=request.listing.listing_id,
                    overall_score=0.0,
                    commute_score=0.0,
                    noise_score=0.0,
                    amenity_score=0.0,
                    social_score=0.0,
                    budget_score=0.0,
                    narrative="Stub: no lifestyle scoring performed",
                ),
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("CalculateLifestyleScore failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
