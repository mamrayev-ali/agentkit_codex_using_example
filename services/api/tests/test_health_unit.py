from decider_api.application.health import get_health_response


def test_health_response_contract_is_exact() -> None:
    assert get_health_response() == {"status": "ok"}
