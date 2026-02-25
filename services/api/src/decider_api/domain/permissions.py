from collections.abc import Iterable, Sequence

SUPPORTED_MODULES: tuple[str, ...] = ("dashboard", "dossiers", "watchlist")

_ADMIN_ROLES = frozenset({"admin"})
_ADMIN_SCOPES = frozenset({"entitlements:write", "entitlements:admin"})
_DOSSIER_ROLES = frozenset({"admin", "analyst", "operator", "user"})
_DOSSIER_SCOPES = frozenset({"read:data"})
_WATCHLIST_ROLES = frozenset({"admin", "analyst", "operator", "viewer"})
_WATCHLIST_SCOPES = frozenset({"watchlist:view"})


def normalize_modules(modules: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for candidate in modules:
        if not isinstance(candidate, str):
            raise ValueError("Module identifiers must be strings.")

        module_key = candidate.strip().lower()
        if not module_key:
            raise ValueError("Module identifier cannot be empty.")
        if module_key not in SUPPORTED_MODULES:
            raise ValueError(f"Unsupported module '{module_key}'.")

        if module_key not in seen:
            normalized.append(module_key)
            seen.add(module_key)

    return normalized


def default_modules_for_claims(*, roles: Sequence[str], scopes: Sequence[str]) -> list[str]:
    role_set = set(roles)
    scope_set = set(scopes)

    modules = ["dashboard"]

    if _DOSSIER_ROLES.intersection(role_set) or _DOSSIER_SCOPES.intersection(scope_set):
        modules.append("dossiers")

    if _WATCHLIST_ROLES.intersection(role_set) or _WATCHLIST_SCOPES.intersection(scope_set):
        modules.append("watchlist")

    return modules


def has_module_access(*, module_key: str, enabled_modules: Sequence[str]) -> bool:
    normalized_key = module_key.strip().lower()
    return normalized_key in set(enabled_modules)


def is_admin_actor(*, roles: Sequence[str], scopes: Sequence[str]) -> bool:
    return bool(_ADMIN_ROLES.intersection(roles) or _ADMIN_SCOPES.intersection(scopes))
