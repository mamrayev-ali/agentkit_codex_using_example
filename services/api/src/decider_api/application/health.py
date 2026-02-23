from typing import Final


_HEALTH_RESPONSE: Final[dict[str, str]] = {"status": "ok"}


def get_health_response() -> dict[str, str]:
    # Return a copy to keep the contract immutable for callers.
    return dict(_HEALTH_RESPONSE)
