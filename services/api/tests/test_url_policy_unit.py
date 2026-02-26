import pytest

from decider_api.domain.url_policy import validate_remote_url


def test_validate_remote_url_allows_public_https_url() -> None:
    validated = validate_remote_url(
        "https://example.com/search?q=acme",
        resolved_ips=["93.184.216.34"],
    )

    assert validated.normalized_url == "https://example.com/search?q=acme"
    assert validated.hostname == "example.com"


def test_validate_remote_url_rejects_blocked_hostname() -> None:
    with pytest.raises(ValueError, match="host is blocked"):
        validate_remote_url("https://localhost/api")


def test_validate_remote_url_rejects_private_ip_literal() -> None:
    with pytest.raises(ValueError, match="blocked IP range"):
        validate_remote_url("http://10.10.10.2/path")


def test_validate_remote_url_rejects_disallowed_scheme() -> None:
    with pytest.raises(ValueError, match="scheme is not allowed"):
        validate_remote_url("ftp://example.com/file")


def test_validate_remote_url_rejects_private_dns_resolution() -> None:
    with pytest.raises(ValueError, match="resolves to a blocked IP range"):
        validate_remote_url(
            "https://example.com/path",
            resolved_ips=["127.0.0.1"],
        )


def test_validate_remote_url_rejects_embedded_credentials() -> None:
    with pytest.raises(ValueError, match="must not include credentials"):
        validate_remote_url("https://user:pass@example.com/data")
