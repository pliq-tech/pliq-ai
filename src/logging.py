"""Structured JSON logging for pliq-ai service."""

import json
import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request-id")


class StructuredFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, str] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": "pliq-ai",
            "request_id": request_id_var.get(),
            "module": record.module,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["error"] = str(record.exc_info[1])
            log_entry["error_type"] = record.exc_info[0].__name__

        return json.dumps(log_entry)


def setup_logging(log_level: str) -> None:
    """Configure the root logger with structured JSON output.

    Args:
        log_level: Logging level name (e.g. "INFO", "DEBUG").
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
