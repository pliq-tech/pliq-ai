import asyncio
import logging
import signal

from src.config import Config
from src.grpc.server import GrpcServer
from src.logging import setup_logging


async def serve() -> None:
    """Start the gRPC server with graceful shutdown."""
    config = Config.from_env()

    setup_logging(config.log_level)
    logger = logging.getLogger("pliq-ai")

    logger.info(
        "Starting pliq-ai gRPC server on %s:%d",
        config.grpc_host,
        config.grpc_port,
    )

    grpc_server = GrpcServer(config)
    await grpc_server.start()

    # Graceful shutdown on SIGTERM / SIGINT
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    await stop_event.wait()
    await grpc_server.stop(grace=5.0)


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
