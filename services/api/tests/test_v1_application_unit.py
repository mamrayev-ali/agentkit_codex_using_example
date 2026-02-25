from decider_api.application.auth_context import get_auth_context_response
from decider_api.application.tenant_resources import list_tenant_base_resources


def test_auth_context_response_is_immutable_between_calls() -> None:
    first = get_auth_context_response()
    assert isinstance(first["scopes"], list)
    assert isinstance(first["roles"], list)
    first["scopes"].append("export:data")
    first["roles"].append("admin")

    second = get_auth_context_response()

    assert second == {
        "authenticated": False,
        "subject": "anonymous",
        "tenant_id": None,
        "scopes": [],
        "roles": [],
    }


def test_tenant_resources_response_is_immutable_between_calls() -> None:
    first = list_tenant_base_resources("acme")
    assert isinstance(first["resources"], list)
    first["resources"].append({"resource_id": "r1", "name": "X"})

    second = list_tenant_base_resources("acme")

    assert second == {
        "tenant_id": "acme",
        "resources": [],
    }
