from collections.abc import Mapping, Sequence


def _append_unique(values: list[str], candidate: str) -> None:
    if candidate and candidate not in values:
        values.append(candidate)


def _extract_scopes(claims: Mapping[str, object]) -> list[str]:
    scopes: list[str] = []

    scope_value = claims.get("scope")
    if isinstance(scope_value, str):
        for scope in scope_value.split():
            _append_unique(scopes, scope)

    scp_value = claims.get("scp")
    if isinstance(scp_value, list):
        for scope in scp_value:
            if isinstance(scope, str):
                _append_unique(scopes, scope)

    return scopes


def _extract_roles(claims: Mapping[str, object]) -> list[str]:
    roles: list[str] = []

    direct_roles = claims.get("roles")
    if isinstance(direct_roles, list):
        for role in direct_roles:
            if isinstance(role, str):
                _append_unique(roles, role)

    realm_access = claims.get("realm_access")
    if isinstance(realm_access, Mapping):
        realm_roles = realm_access.get("roles")
        if isinstance(realm_roles, list):
            for role in realm_roles:
                if isinstance(role, str):
                    _append_unique(roles, role)

    resource_access = claims.get("resource_access")
    if isinstance(resource_access, Mapping):
        for client_data in resource_access.values():
            if not isinstance(client_data, Mapping):
                continue
            client_roles = client_data.get("roles")
            if isinstance(client_roles, list):
                for role in client_roles:
                    if isinstance(role, str):
                        _append_unique(roles, role)

    return roles


def _extract_tenant_id(
    claims: Mapping[str, object],
    tenant_claim_names: Sequence[str],
) -> str | None:
    for claim_name in tenant_claim_names:
        value = claims.get(claim_name)
        if isinstance(value, str) and value:
            return value
    return None


def build_auth_context_response(
    claims: Mapping[str, object],
    tenant_claim_names: Sequence[str],
) -> dict[str, object]:
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise ValueError("Token subject claim is required.")

    return {
        "authenticated": True,
        "subject": subject,
        "tenant_id": _extract_tenant_id(claims, tenant_claim_names),
        "scopes": _extract_scopes(claims),
        "roles": _extract_roles(claims),
    }
