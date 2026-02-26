from dataclasses import dataclass
from uuid import uuid4

from decider_api.domain.source_adapter import SourceAdapter
from decider_api.domain.url_policy import validate_remote_url


@dataclass(frozen=True)
class IngestionJobRequest:
    tenant_id: str
    source_key: str
    remote_url: str
    requested_by: str


def _normalize_required_value(*, value: str, field_name: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} cannot be empty.")
    return normalized_value


def build_ingestion_job_payload(request: IngestionJobRequest) -> dict[str, str]:
    tenant_id = _normalize_required_value(value=request.tenant_id, field_name="tenant_id")
    source_key = _normalize_required_value(value=request.source_key, field_name="source_key")
    requested_by = _normalize_required_value(
        value=request.requested_by,
        field_name="requested_by",
    )

    validated_url = validate_remote_url(request.remote_url)

    return {
        "job_id": f"ingestion-{uuid4().hex[:12]}",
        "tenant_id": tenant_id,
        "source_key": source_key,
        "remote_url": validated_url.normalized_url,
        "requested_by": requested_by,
    }


def process_ingestion_job(
    *,
    job_payload: dict[str, str],
    source_adapter: SourceAdapter,
) -> dict[str, object]:
    job_id = _normalize_required_value(
        value=job_payload.get("job_id", ""),
        field_name="job_id",
    )
    tenant_id = _normalize_required_value(
        value=job_payload.get("tenant_id", ""),
        field_name="tenant_id",
    )
    source_key = _normalize_required_value(
        value=job_payload.get("source_key", ""),
        field_name="source_key",
    )
    requested_by = _normalize_required_value(
        value=job_payload.get("requested_by", ""),
        field_name="requested_by",
    )
    remote_url = _normalize_required_value(
        value=job_payload.get("remote_url", ""),
        field_name="remote_url",
    )

    fetch_result = source_adapter.fetch(source_key=source_key, remote_url=remote_url)
    return {
        "job_id": job_id,
        "tenant_id": tenant_id,
        "source_key": source_key,
        "requested_by": requested_by,
        "remote_url": fetch_result.requested_url,
        "status": "completed",
        "http_status": fetch_result.status_code,
        "content_type": fetch_result.content_type,
        "content_length": len(fetch_result.body),
    }
