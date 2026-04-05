"""gRPC handler for FraudDetectionService."""

import logging

import grpc

from src.config import Config
from src import fraud_detection_pb2
from src import fraud_detection_pb2_grpc

logger = logging.getLogger(__name__)


class FraudDetectionHandler(
    fraud_detection_pb2_grpc.FraudDetectionServiceServicer,
):
    """Stub implementation of the FraudDetectionService."""

    def __init__(self, config: Config) -> None:
        self._config = config

    async def AnalyzeImage(
        self,
        request: fraud_detection_pb2.AnalyzeImageRequest,
        context: grpc.aio.ServicerContext,
    ) -> fraud_detection_pb2.FraudReport:
        """Analyze an image for manipulation indicators."""
        try:
            if not request.image_data:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "image_data is required",
                )
            if not request.listing_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "listing_id is required",
                )

            logger.info(
                "AnalyzeImage: listing_id=%s request_id=%s",
                request.listing_id,
                request.request_id,
            )

            return fraud_detection_pb2.FraudReport(
                request_id=request.request_id,
                overall_score=0.0,
                ela=fraud_detection_pb2.ELAResult(score=0.0, details="placeholder"),
                fft=fraud_detection_pb2.FFTResult(score=0.0, details="placeholder"),
                exif=fraud_detection_pb2.EXIFResult(score=0.0, details="placeholder"),
                reverse_image=fraud_detection_pb2.ReverseImageResult(
                    score=0.0, details="placeholder"
                ),
                explanation="Stub: no analysis performed",
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("AnalyzeImage failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def DetectPriceAnomaly(
        self,
        request: fraud_detection_pb2.PriceAnomalyRequest,
        context: grpc.aio.ServicerContext,
    ) -> fraud_detection_pb2.PriceAnomalyReport:
        """Detect price anomalies in a listing."""
        try:
            if not request.listing_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "listing_id is required",
                )
            if request.listing_price <= 0:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "listing_price must be positive",
                )

            logger.info(
                "DetectPriceAnomaly: listing_id=%s request_id=%s",
                request.listing_id,
                request.request_id,
            )

            return fraud_detection_pb2.PriceAnomalyReport(
                request_id=request.request_id,
                anomaly_score=0.0,
                market_median=0.0,
                market_std_dev=0.0,
                z_score=0.0,
                comparable_count=0,
                confidence=0.0,
                explanation="Stub: no anomaly detection performed",
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("DetectPriceAnomaly failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def DetectDuplicateListing(
        self,
        request: fraud_detection_pb2.DuplicateListingRequest,
        context: grpc.aio.ServicerContext,
    ) -> fraud_detection_pb2.DuplicateReport:
        """Detect duplicate listings."""
        try:
            if not request.listing_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "listing_id is required",
                )
            if not request.title and not request.description:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "title or description is required",
                )

            logger.info(
                "DetectDuplicateListing: listing_id=%s request_id=%s",
                request.listing_id,
                request.request_id,
            )

            return fraud_detection_pb2.DuplicateReport(
                request_id=request.request_id,
                duplication_score=0.0,
                text_similarity=0.0,
                image_similarity=0.0,
                location_proximity=0.0,
                summary="Stub: no duplication detection performed",
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("DetectDuplicateListing failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
