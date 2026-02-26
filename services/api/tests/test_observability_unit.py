import json
import logging
import re

from decider_api.infrastructure.observability.correlation import (
    normalize_correlation_id,
    resolve_correlation_id,
)
from decider_api.infrastructure.observability.exceptions import (
    LoggingExceptionReporter,
    NoopExceptionReporter,
    build_exception_reporter,
)
from decider_api.infrastructure.observability.logging import JsonLogFormatter


def test_normalize_correlation_id_accepts_safe_identifier() -> None:
    assert normalize_correlation_id("trace-123._abc") == "trace-123._abc"


def test_normalize_correlation_id_rejects_unsafe_identifier() -> None:
    assert normalize_correlation_id("bad value with spaces") is None


def test_resolve_correlation_id_generates_identifier_for_invalid_input() -> None:
    generated = resolve_correlation_id("invalid value")

    assert generated
    assert re.fullmatch(r"[A-Za-z0-9._-]{1,128}", generated) is not None


def test_json_log_formatter_emits_structured_payload() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="decider_api.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.event = "http.request.completed"
    record.correlation_id = "trace-1"
    record.http_method = "GET"
    record.http_route = "/api/v1/health"
    record.status_code = 200

    payload = json.loads(formatter.format(record))

    assert payload["event"] == "http.request.completed"
    assert payload["correlation_id"] == "trace-1"
    assert payload["http_method"] == "GET"
    assert payload["http_route"] == "/api/v1/health"
    assert payload["status_code"] == 200


def test_logging_exception_reporter_emits_error_event(caplog) -> None:
    caplog.set_level(logging.ERROR, logger="decider_api.exceptions")
    reporter = build_exception_reporter(enabled=True)

    assert isinstance(reporter, LoggingExceptionReporter)

    try:
        raise RuntimeError("boom")
    except RuntimeError as exc:
        reporter.report(
            exc=exc,
            correlation_id="trace-exc-1",
            http_method="GET",
            http_route="/explode",
        )

    records = [
        record
        for record in caplog.records
        if getattr(record, "event", None) == "http.request.unhandled_exception"
    ]
    assert records
    assert getattr(records[-1], "correlation_id", None) == "trace-exc-1"
    assert getattr(records[-1], "error_type", None) == "RuntimeError"


def test_noop_exception_reporter_is_returned_when_disabled() -> None:
    reporter = build_exception_reporter(enabled=False)

    assert isinstance(reporter, NoopExceptionReporter)
