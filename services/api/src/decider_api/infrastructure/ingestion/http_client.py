from collections.abc import Callable
from dataclasses import dataclass
import time

import httpx


_RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


@dataclass(frozen=True)
class RetryPolicy:
    timeout_seconds: float
    max_retries: int
    backoff_seconds: float


class RetryingHttpClient:
    def __init__(
        self,
        *,
        retry_policy: RetryPolicy,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if retry_policy.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_policy.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if retry_policy.backoff_seconds < 0:
            raise ValueError("backoff_seconds must be >= 0")

        self._retry_policy = retry_policy
        self._transport = transport
        self._sleep = sleep

    def get(self, url: str) -> httpx.Response:
        last_error: Exception | None = None
        attempts = self._retry_policy.max_retries + 1

        for attempt in range(attempts):
            try:
                with httpx.Client(
                    timeout=self._retry_policy.timeout_seconds,
                    transport=self._transport,
                    follow_redirects=True,
                ) as client:
                    response = client.get(url)

                if response.status_code in _RETRYABLE_STATUS_CODES and attempt < attempts - 1:
                    self._sleep(self._retry_policy.backoff_seconds * (2**attempt))
                    continue

                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                if isinstance(exc, httpx.HTTPStatusError):
                    status_code = exc.response.status_code
                    should_retry = (
                        status_code in _RETRYABLE_STATUS_CODES and attempt < attempts - 1
                    )
                    if not should_retry:
                        raise
                else:
                    if attempt >= attempts - 1:
                        raise

                self._sleep(self._retry_policy.backoff_seconds * (2**attempt))
                last_error = exc

        if last_error is not None:
            raise last_error

        raise RuntimeError("RetryingHttpClient failed without an explicit exception.")
