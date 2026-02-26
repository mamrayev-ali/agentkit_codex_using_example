import json
import logging
from datetime import datetime, timezone

from decider_api.infrastructure.observability.correlation import get_correlation_id

_DEFAULT_CORRELATION_ID = "-"
_STRUCTURED_LOGGING_CONFIGURED = False
_STANDARD_LOG_RECORD_FIELDS = set(logging.LogRecord(
    name="",
    level=0,
    pathname="",
    lineno=0,
    msg="",
    args=(),
    exc_info=None,
).__dict__.keys()) | {"message", "asctime"}


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = get_correlation_id()
        if correlation_id is not None and correlation_id:
            record.correlation_id = correlation_id
        elif not hasattr(record, "correlation_id"):
            record.correlation_id = _DEFAULT_CORRELATION_ID
        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self._format_utc_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", _DEFAULT_CORRELATION_ID),
        }

        for key, value in record.__dict__.items():
            if key in _STANDARD_LOG_RECORD_FIELDS:
                continue
            if key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = self._normalize_value(value)

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))

    @staticmethod
    def _format_utc_timestamp(created: float) -> str:
        return (
            datetime.fromtimestamp(created, tz=timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    @staticmethod
    def _normalize_value(value: object) -> object:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)


def configure_structured_logging(level_name: str) -> None:
    global _STRUCTURED_LOGGING_CONFIGURED

    if _STRUCTURED_LOGGING_CONFIGURED:
        return

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(CorrelationIdFilter())
    root_logger.addHandler(handler)

    level = getattr(logging, level_name.upper(), logging.INFO)
    root_logger.setLevel(level)

    _STRUCTURED_LOGGING_CONFIGURED = True
