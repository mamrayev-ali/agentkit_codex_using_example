from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "Decider API"
    public_api_prefix: str = "/api/v1"
    public_api_version: str = "1.0.0"


def get_settings() -> AppSettings:
    return AppSettings()
