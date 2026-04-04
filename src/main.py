import asyncio
import logging
import signal
import sys

from src.config import Config


async def serve() -> None:
    """Start the gRPC server."""
    config = Config.from_env()

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger("pliq-ai")

    logger.info(
        "Starting pliq-ai gRPC server on %s:%d",
        config.grpc_host,
        config.grpc_port,
    )

    try:
        import grpc
        from grpc_health.v1 import health_pb2, health_pb2_grpc
        from grpc_health.v1.health import HealthServicer

        server = grpc.aio.server()

        # Register health check
        health_servicer = HealthServicer()
        health_pb2_grpc.add_HealthServicer_to_server(health_servicer, server)
        health_servicer.set(
            "", health_pb2.HealthCheckResponse.SERVING
        )

        server.add_insecure_port(f"{config.grpc_host}:{config.grpc_port}")
        await server.start()

        logger.info("gRPC server started successfully")

        # Graceful shutdown
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        def _signal_handler() -> None:
            logger.info("Shutdown signal received")
            stop_event.set()

        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, _signal_handler)

        await stop_event.wait()
        logger.info("Shutting down gRPC server...")
        await server.stop(grace=5)
        logger.info("Server stopped")

    except ImportError:
        logger.warning("grpc not available, running in stub mode")
        logger.info("pliq-ai service ready (stub mode)")
        await asyncio.Event().wait()


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
