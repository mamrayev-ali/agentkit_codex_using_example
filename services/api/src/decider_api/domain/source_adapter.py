from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SourceFetchResult:
    source_key: str
    requested_url: str
    status_code: int
    content_type: str
    body: bytes


class SourceAdapter(Protocol):
    def fetch(self, *, source_key: str, remote_url: str) -> SourceFetchResult:
        ...
