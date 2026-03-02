import logging
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from decider_api.api.routes.health import router as health_router
from decider_api.api.routes.v1 import router as v1_router
from decider_api.infrastructure.observability.correlation import (
    reset_correlation_id,
    resolve_correlation_id,
    set_correlation_id,
)
from decider_api.infrastructure.observability.exceptions import build_exception_reporter
from decider_api.infrastructure.observability.logging import configure_structured_logging
from decider_api.infrastructure.observability.metrics import InMemoryMetricsRegistry
from decider_api.settings import get_settings


def _resolve_http_route_template(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if isinstance(route_path, str) and route_path:
        return route_path
    return request.url.path


def create_app() -> FastAPI:
    settings = get_settings()
    if (
        settings.observability_enable_request_logging
        or settings.observability_enable_exception_reporting
    ):
        configure_structured_logging(settings.observability_log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.public_api_version,
    )
    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allow_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type"],
        )
    metrics_registry = InMemoryMetricsRegistry()
    exception_reporter = build_exception_reporter(
        enabled=settings.observability_enable_exception_reporting
    )
    access_logger = logging.getLogger("decider_api.access")

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        correlation_id = resolve_correlation_id(
            request.headers.get(settings.observability_correlation_header)
        )
        context_token = set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        response = None
        status_code = 500
        started_at = perf_counter()

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[settings.observability_correlation_header] = correlation_id
            return response
        except Exception as exc:
            exception_reporter.report(
                exc=exc,
                correlation_id=correlation_id,
                http_method=request.method,
                http_route=_resolve_http_route_template(request),
            )
            raise
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            route_template = _resolve_http_route_template(request)

            if settings.observability_enable_metrics:
                metrics_registry.record_request(
                    method=request.method,
                    route=route_template,
                    status_code=status_code,
                    duration_ms=duration_ms,
                )

            if settings.observability_enable_request_logging:
                access_logger.info(
                    "request_completed",
                    extra={
                        "event": "http.request.completed",
                        "correlation_id": correlation_id,
                        "http_method": request.method,
                        "http_route": route_template,
                        "status_code": status_code,
                        "duration_ms": round(duration_ms, 3),
                    },
                )

            reset_correlation_id(context_token)

    if settings.observability_enable_metrics:

        @app.get("/metrics", include_in_schema=False)
        def get_metrics() -> PlainTextResponse:
            return PlainTextResponse(
                content=metrics_registry.render_prometheus(),
                media_type="text/plain; version=0.0.4; charset=utf-8",
            )

    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.public_api_prefix)
    return app


app = create_app()
