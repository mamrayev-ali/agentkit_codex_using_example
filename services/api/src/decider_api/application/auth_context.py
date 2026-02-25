from typing import Final


_DEFAULT_AUTH_CONTEXT: Final[dict[str, object]] = {
    "authenticated": False,
    "subject": "anonymous",
    "tenant_id": None,
    "scopes": [],
    "roles": [],
}


def get_auth_context_response() -> dict[str, object]:
    # Return a deep-enough copy so list fields cannot mutate shared defaults.
    scopes = list(_DEFAULT_AUTH_CONTEXT["scopes"])
    roles = list(_DEFAULT_AUTH_CONTEXT["roles"])
    return {
        "authenticated": _DEFAULT_AUTH_CONTEXT["authenticated"],
        "subject": _DEFAULT_AUTH_CONTEXT["subject"],
        "tenant_id": _DEFAULT_AUTH_CONTEXT["tenant_id"],
        "scopes": scopes,
        "roles": roles,
    }
