from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    app_name: str = "decider-api"


def get_settings() -> AppSettings:
    return AppSettings()
