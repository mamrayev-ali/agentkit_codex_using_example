import logging
from dataclasses import dataclass


class ExceptionReporter:
    def report(
        self,
        *,
        exc: Exception,
        correlation_id: str,
        http_method: str,
        http_route: str,
    ) -> None:
        raise NotImplementedError


class NoopExceptionReporter(ExceptionReporter):
    def report(
        self,
        *,
        exc: Exception,
        correlation_id: str,
        http_method: str,
        http_route: str,
    ) -> None:
        return


@dataclass(frozen=True)
class LoggingExceptionReporter(ExceptionReporter):
    logger: logging.Logger

    def report(
        self,
        *,
        exc: Exception,
        correlation_id: str,
        http_method: str,
        http_route: str,
    ) -> None:
        self.logger.exception(
            "request_unhandled_exception",
            extra={
                "event": "http.request.unhandled_exception",
                "correlation_id": correlation_id,
                "http_method": http_method,
                "http_route": http_route,
                "error_type": type(exc).__name__,
            },
        )


def build_exception_reporter(*, enabled: bool) -> ExceptionReporter:
    if not enabled:
        return NoopExceptionReporter()

    return LoggingExceptionReporter(logger=logging.getLogger("decider_api.exceptions"))
