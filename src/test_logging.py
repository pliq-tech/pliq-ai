"""Unit tests for src.logging structured logging."""

import json
import logging

import pytest

from src.logging import StructuredFormatter, request_id_var, setup_logging


@pytest.fixture(autouse=True)
def _reset_request_id() -> None:
    """Reset request_id_var to default before each test."""
    token = request_id_var.set("no-request-id")
    yield
    request_id_var.reset(token)


@pytest.fixture()
def _clean_root_logger() -> None:
    """Remove handlers added by setup_logging after test."""
    root = logging.getLogger()
    original_handlers = list(root.handlers)
    original_level = root.level
    yield
    root.handlers = original_handlers
    root.setLevel(original_level)


def _make_log_record(
    message: str = "test message",
    level: int = logging.INFO,
    module: str = "test_module",
) -> logging.LogRecord:
    """Create a LogRecord for testing the formatter."""
    return logging.LogRecord(
        name="test",
        level=level,
        pathname="test_module.py",
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )


def test_structured_formatter_json_output() -> None:
    """Formatter produces valid JSON with all required fields."""
    # Arrange
    formatter = StructuredFormatter()
    record = _make_log_record(message="hello world")

    # Act
    output = formatter.format(record)
    parsed = json.loads(output)

    # Assert
    assert parsed["level"] == "INFO"
    assert parsed["service"] == "pliq-ai"
    assert parsed["message"] == "hello world"
    assert parsed["request_id"] == "no-request-id"
    assert "timestamp" in parsed
    assert "module" in parsed


def test_request_id_included() -> None:
    """request_id_var value appears in formatted log output."""
    # Arrange
    formatter = StructuredFormatter()
    request_id_var.set("req-abc-789")
    record = _make_log_record()

    # Act
    output = formatter.format(record)
    parsed = json.loads(output)

    # Assert
    assert parsed["request_id"] == "req-abc-789"


def test_error_fields_included_on_exception() -> None:
    """error and error_type fields appear when exc_info is set."""
    # Arrange
    formatter = StructuredFormatter()
    try:
        raise ValueError("bad value")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

    record = _make_log_record(message="operation failed")
    record.exc_info = exc_info

    # Act
    output = formatter.format(record)
    parsed = json.loads(output)

    # Assert
    assert parsed["error"] == "bad value"
    assert parsed["error_type"] == "ValueError"
    assert parsed["message"] == "operation failed"


def test_no_error_fields_without_exception() -> None:
    """error and error_type fields are absent when no exception."""
    # Arrange
    formatter = StructuredFormatter()
    record = _make_log_record()

    # Act
    output = formatter.format(record)
    parsed = json.loads(output)

    # Assert
    assert "error" not in parsed
    assert "error_type" not in parsed


@pytest.mark.usefixtures("_clean_root_logger")
def test_setup_logging_configures_handler() -> None:
    """setup_logging adds a StreamHandler with StructuredFormatter to root."""
    # Arrange
    root = logging.getLogger()
    handler_count_before = len(root.handlers)

    # Act
    setup_logging("DEBUG")

    # Assert
    assert len(root.handlers) == handler_count_before + 1
    new_handler = root.handlers[-1]
    assert isinstance(new_handler, logging.StreamHandler)
    assert isinstance(new_handler.formatter, StructuredFormatter)
    assert root.level == logging.DEBUG


@pytest.mark.usefixtures("_clean_root_logger")
def test_setup_logging_level_case_insensitive() -> None:
    """setup_logging accepts level names in any case."""
    # Arrange & Act
    setup_logging("warning")

    # Assert
    root = logging.getLogger()
    assert root.level == logging.WARNING
