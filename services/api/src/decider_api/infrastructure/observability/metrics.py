from collections import Counter
from threading import Lock
from time import monotonic


class InMemoryMetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._request_total: Counter[tuple[str, str, str]] = Counter()
        self._request_duration_ms_sum: Counter[tuple[str, str]] = Counter()
        self._started_at = monotonic()

    def record_request(
        self,
        *,
        method: str,
        route: str,
        status_code: int,
        duration_ms: float,
    ) -> None:
        normalized_method = method.upper()
        normalized_route = route or "unknown"
        normalized_status_code = str(status_code)

        with self._lock:
            request_key = (
                normalized_method,
                normalized_route,
                normalized_status_code,
            )
            duration_key = (
                normalized_method,
                normalized_route,
            )
            self._request_total[request_key] += 1
            self._request_duration_ms_sum[duration_key] += max(duration_ms, 0.0)

    def render_prometheus(self) -> str:
        lines: list[str] = []
        lines.append(
            "# HELP decider_http_requests_total Total number of HTTP requests by method, route, and status code."
        )
        lines.append("# TYPE decider_http_requests_total counter")

        with self._lock:
            request_items = sorted(self._request_total.items())
            duration_items = sorted(self._request_duration_ms_sum.items())

        for (method, route, status_code), count in request_items:
            lines.append(
                "decider_http_requests_total"
                f"{{method=\"{_escape_label(method)}\",route=\"{_escape_label(route)}\",status_code=\"{_escape_label(status_code)}\"}} {count}"
            )

        lines.append(
            "# HELP decider_http_request_duration_ms_sum Sum of HTTP request duration in milliseconds by method and route."
        )
        lines.append("# TYPE decider_http_request_duration_ms_sum counter")

        for (method, route), duration_sum in duration_items:
            lines.append(
                "decider_http_request_duration_ms_sum"
                f"{{method=\"{_escape_label(method)}\",route=\"{_escape_label(route)}\"}} {duration_sum:.3f}"
            )

        lines.append("# HELP decider_process_uptime_seconds Process uptime in seconds.")
        lines.append("# TYPE decider_process_uptime_seconds gauge")
        lines.append(f"decider_process_uptime_seconds {max(monotonic() - self._started_at, 0.0):.3f}")

        return "\n".join(lines) + "\n"


def _escape_label(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace('"', '\\"')
    )
