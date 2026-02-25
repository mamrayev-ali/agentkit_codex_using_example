from typing import Final


_DEFAULT_RESOURCES: Final[list[dict[str, str]]] = []


def list_tenant_base_resources(tenant_id: str) -> dict[str, object]:
    # Return a fresh list so response payloads stay immutable for callers.
    resources = [dict(item) for item in _DEFAULT_RESOURCES]
    return {
        "tenant_id": tenant_id,
        "resources": resources,
    }
