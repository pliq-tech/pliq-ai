"""gRPC handler for LeaseAnalysisService."""

import logging

import grpc

from src.config import Config
from src import lease_analysis_pb2
from src import lease_analysis_pb2_grpc

logger = logging.getLogger(__name__)


class LeaseAnalysisHandler(
    lease_analysis_pb2_grpc.LeaseAnalysisServiceServicer,
):
    """Stub implementation of the LeaseAnalysisService."""

    def __init__(self, config: Config) -> None:
        self._config = config

    async def AnalyzeClauses(
        self,
        request: lease_analysis_pb2.ClauseAnalysisRequest,
        context: grpc.aio.ServicerContext,
    ) -> lease_analysis_pb2.ClauseAnalysisResponse:
        """Analyze lease text for risky clauses."""
        try:
            if not request.lease_text:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "lease_text is required",
                )
            if not request.language:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "language is required (e.g. 'fr', 'en')",
                )

            logger.info(
                "AnalyzeClauses: language=%s text_len=%d request_id=%s",
                request.language,
                len(request.lease_text),
                request.request_id,
            )

            return lease_analysis_pb2.ClauseAnalysisResponse(
                request_id=request.request_id,
                clauses=[],
                overall_assessment="Stub: no clause analysis performed",
                high_risk_count=0,
                medium_risk_count=0,
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("AnalyzeClauses failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))

    async def CompareConditionReports(
        self,
        request: lease_analysis_pb2.ConditionReportRequest,
        context: grpc.aio.ServicerContext,
    ) -> lease_analysis_pb2.ConditionReportResponse:
        """Compare check-in and check-out condition report photos."""
        try:
            if not request.lease_id:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "lease_id is required",
                )
            if not request.check_in:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "check_in photos are required",
                )
            if not request.check_out:
                await context.abort(
                    grpc.StatusCode.INVALID_ARGUMENT,
                    "check_out photos are required",
                )

            logger.info(
                "CompareConditionReports: lease_id=%s rooms_in=%d rooms_out=%d request_id=%s",
                request.lease_id,
                len(request.check_in),
                len(request.check_out),
                request.request_id,
            )

            return lease_analysis_pb2.ConditionReportResponse(
                request_id=request.request_id,
                rooms=[],
                overall_summary="Stub: no condition comparison performed",
                total_estimated_cost_min=0.0,
                total_estimated_cost_max=0.0,
            )
        except grpc.aio.AbortError:
            raise
        except Exception as exc:
            logger.exception("CompareConditionReports failed: %s", exc)
            await context.abort(grpc.StatusCode.INTERNAL, str(exc))
