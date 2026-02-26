from collections.abc import Callable
import socket

from decider_api.domain.source_adapter import SourceAdapter, SourceFetchResult
from decider_api.domain.url_policy import validate_remote_url
from decider_api.infrastructure.ingestion.http_client import RetryingHttpClient


class HttpSourceAdapter(SourceAdapter):
    def __init__(
        self,
        *,
        http_client: RetryingHttpClient,
        resolve_host: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._http_client = http_client
        self._resolve_host = resolve_host or _resolve_public_ips

    def fetch(self, *, source_key: str, remote_url: str) -> SourceFetchResult:
        resolved_ips = self._resolve_host(_extract_hostname(remote_url))
        validated_url = validate_remote_url(remote_url, resolved_ips=resolved_ips)

        response = self._http_client.get(validated_url.normalized_url)
        content_type = response.headers.get("content-type", "application/octet-stream")
        return SourceFetchResult(
            source_key=source_key,
            requested_url=validated_url.normalized_url,
            status_code=response.status_code,
            content_type=content_type,
            body=response.content,
        )


def _extract_hostname(remote_url: str) -> str:
    validated_url = validate_remote_url(remote_url)
    return validated_url.hostname


def _resolve_public_ips(hostname: str) -> list[str]:
    try:
        address_infos = socket.getaddrinfo(hostname, None)
    except OSError as exc:
        raise ValueError("Remote URL host resolution failed.") from exc

    resolved_ips: list[str] = []
    for address_info in address_infos:
        socket_address = address_info[4]
        if not socket_address:
            continue

        host_ip = socket_address[0]
        if isinstance(host_ip, str) and host_ip:
            resolved_ips.append(host_ip)

    # Preserve order while de-duplicating.
    return list(dict.fromkeys(resolved_ips))
