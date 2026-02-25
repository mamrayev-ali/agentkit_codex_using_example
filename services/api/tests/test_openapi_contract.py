import json
from pathlib import Path

import pytest

from decider_api.app import app


OPENAPI_CONTRACT_PATH = (
    Path(__file__).resolve().parents[1] / "openapi" / "openapi.v1.json"
)
REQUIRED_V1_PATHS = {
    "/api/v1/health",
    "/api/v1/auth/context",
    "/api/v1/tenants/{tenant_id}/resources",
}


def _load_openapi_contract() -> dict[str, object]:
    return json.loads(OPENAPI_CONTRACT_PATH.read_text(encoding="utf-8"))


@pytest.mark.smoke
def test_openapi_contract_file_is_valid_and_v1_scoped() -> None:
    contract = _load_openapi_contract()

    assert isinstance(contract.get("openapi"), str)
    assert contract["openapi"].startswith("3.")
    assert contract["info"]["version"] == "1.0.0"

    paths = contract.get("paths", {})
    assert REQUIRED_V1_PATHS.issubset(paths.keys())
    assert all(path.startswith("/api/v1/") for path in paths.keys())


def test_runtime_openapi_matches_checked_in_contract() -> None:
    contract = _load_openapi_contract()

    assert app.openapi() == contract
