"""Async gRPC server for pliq-ai service."""

import logging
from contextvars import ContextVar

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc
from grpc_health.v1.health import HealthServicer

from src.config import Config
from src.grpc.handlers.fraud_handler import FraudDetectionHandler
from src.grpc.handlers.lease_handler import LeaseAnalysisHandler
from src.grpc.handlers.matching_handler import MatchingHandler
from src.grpc.handlers.search_handler import SearchHandler

logger = logging.getLogger(__name__)

request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request-id")


def _extract_request_id(context: grpc.aio.ServicerContext) -> str:
    """Extract request_id from gRPC metadata, falling back to a default."""
    metadata = context.invocation_metadata()
    if metadata:
        for key, value in metadata:
            if key == "x-request-id":
                return value
    return "no-request-id"


class RequestLoggingInterceptor(grpc.aio.ServerInterceptor):
    """Interceptor that logs each request and sets request_id context var."""

    async def intercept_service(
        self,
        continuation,
        handler_call_details: grpc.HandlerCallDetails,
    ):
        method = handler_call_details.method
        metadata = handler_call_details.invocation_metadata
        rid = "no-request-id"
        if metadata:
            for key, value in metadata:
                if key == "x-request-id":
                    rid = value
                    break

        request_id_var.set(rid)
        logger.info("gRPC request: method=%s request_id=%s", method, rid)
        return await continuation(handler_call_details)


def _register_services(server: grpc.aio.Server, config: Config) -> None:
    """Register all service handlers on the gRPC server."""
    from src import fraud_detection_pb2_grpc
    from src import lease_analysis_pb2_grpc
    from src import matching_pb2_grpc
    from src import search_pb2_grpc

    fraud_detection_pb2_grpc.add_FraudDetectionServiceServicer_to_server(
        FraudDetectionHandler(config), server
    )
    matching_pb2_grpc.add_MatchingServiceServicer_to_server(
        MatchingHandler(config), server
    )
    lease_analysis_pb2_grpc.add_LeaseAnalysisServiceServicer_to_server(
        LeaseAnalysisHandler(config), server
    )
    search_pb2_grpc.add_SearchServiceServicer_to_server(
        SearchHandler(config), server
    )


class GrpcServer:
    """Async gRPC server wrapper for pliq-ai."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._server: grpc.aio.Server | None = None

    async def start(self) -> None:
        """Create, configure, and start the gRPC server."""
        interceptors = [RequestLoggingInterceptor()]
        self._server = grpc.aio.server(interceptors=interceptors)

        # Health checking
        health_servicer = HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, self._server)
        health_servicer.set("", health_pb2.HealthCheckResponse.SERVING)

        # Application services
        _register_services(self._server, self._config)

        bind_address = f"{self._config.grpc_host}:{self._config.grpc_port}"
        self._server.add_insecure_port(bind_address)
        await self._server.start()
        logger.info("gRPC server listening on %s", bind_address)

    async def stop(self, grace: float = 5.0) -> None:
        """Gracefully stop the gRPC server."""
        if self._server:
            logger.info("Stopping gRPC server (grace=%.1fs)...", grace)
            await self._server.stop(grace=grace)
            logger.info("gRPC server stopped")

    async def wait_for_termination(self) -> None:
        """Block until the server terminates."""
        if self._server:
            await self._server.wait_for_termination()
