import httpx
import pytest

from decider_api.infrastructure.ingestion.http_client import RetryPolicy, RetryingHttpClient


def test_retrying_http_client_retries_retryable_status_codes() -> None:
    call_count = {"value": 0}
    sleep_calls: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        if call_count["value"] == 1:
            return httpx.Response(status_code=503, request=request, text="retry")
        return httpx.Response(status_code=200, request=request, text="ok")

    client = RetryingHttpClient(
        retry_policy=RetryPolicy(timeout_seconds=1.0, max_retries=2, backoff_seconds=0.25),
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: sleep_calls.append(seconds),
    )

    response = client.get("https://example.com")

    assert response.status_code == 200
    assert call_count["value"] == 2
    assert sleep_calls == [0.25]


def test_retrying_http_client_raises_after_transport_retries_exhausted() -> None:
    call_count = {"value": 0}
    sleep_calls: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        raise httpx.ReadTimeout("timeout", request=request)

    client = RetryingHttpClient(
        retry_policy=RetryPolicy(timeout_seconds=1.0, max_retries=2, backoff_seconds=0.1),
        transport=httpx.MockTransport(handler),
        sleep=lambda seconds: sleep_calls.append(seconds),
    )

    with pytest.raises(httpx.ReadTimeout):
        client.get("https://example.com")

    assert call_count["value"] == 3
    assert sleep_calls == [0.1, 0.2]


def test_retrying_http_client_does_not_retry_non_retryable_http_errors() -> None:
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        return httpx.Response(status_code=404, request=request, text="not found")

    client = RetryingHttpClient(
        retry_policy=RetryPolicy(timeout_seconds=1.0, max_retries=3, backoff_seconds=0.1),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(httpx.HTTPStatusError):
        client.get("https://example.com")

    assert call_count["value"] == 1
