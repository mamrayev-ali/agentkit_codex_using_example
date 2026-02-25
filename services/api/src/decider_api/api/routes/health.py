from fastapi import APIRouter

from decider_api.application.health import get_health_response

router = APIRouter()


@router.get("/health", include_in_schema=False)
def get_health() -> dict[str, str]:
    return get_health_response()
