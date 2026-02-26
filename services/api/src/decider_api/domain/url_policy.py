from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Sequence
from urllib.parse import urlparse


_BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "localhost.localdomain",
        "metadata.google.internal",
    }
)
_ALLOWED_SCHEMES = frozenset({"http", "https"})


@dataclass(frozen=True)
class ValidatedRemoteUrl:
    normalized_url: str
    hostname: str


def _is_blocked_ip(raw_address: str) -> bool:
    parsed_address = ip_address(raw_address)
    return not parsed_address.is_global


def _parse_ip_literal(raw_address: str) -> IPv4Address | IPv6Address | None:
    try:
        return ip_address(raw_address)
    except ValueError:
        return None


def validate_remote_url(
    remote_url: str,
    *,
    resolved_ips: Sequence[str] | None = None,
) -> ValidatedRemoteUrl:
    normalized_url = remote_url.strip()
    if not normalized_url:
        raise ValueError("Remote URL cannot be empty.")

    parsed_url = urlparse(normalized_url)
    scheme = parsed_url.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError("Remote URL scheme is not allowed.")

    hostname = parsed_url.hostname
    if hostname is None:
        raise ValueError("Remote URL must include a host.")

    normalized_hostname = hostname.strip().lower()
    if not normalized_hostname:
        raise ValueError("Remote URL must include a host.")

    if parsed_url.username or parsed_url.password:
        raise ValueError("Remote URL must not include credentials.")

    if normalized_hostname in _BLOCKED_HOSTNAMES:
        raise ValueError("Remote URL host is blocked.")

    if normalized_hostname.endswith(".local"):
        raise ValueError("Remote URL host is blocked.")

    ip_literal = _parse_ip_literal(normalized_hostname)
    if ip_literal is not None and not ip_literal.is_global:
        raise ValueError("Remote URL points to a blocked IP range.")

    if resolved_ips is not None:
        if not resolved_ips:
            raise ValueError("Remote URL host did not resolve to an address.")

        for resolved_ip in resolved_ips:
            if _parse_ip_literal(resolved_ip) is None:
                raise ValueError("Remote URL host resolved to an invalid IP address.")
            if _is_blocked_ip(resolved_ip):
                raise ValueError("Remote URL host resolves to a blocked IP range.")

    return ValidatedRemoteUrl(
        normalized_url=normalized_url,
        hostname=normalized_hostname,
    )
