from contextvars import ContextVar, Token
from re import Pattern, compile
from uuid import uuid4

_CORRELATION_ID_CONTEXT: ContextVar[str | None] = ContextVar(
    "decider_correlation_id",
    default=None,
)
_ALLOWED_CORRELATION_ID_PATTERN: Pattern[str] = compile(r"^[A-Za-z0-9._-]{1,128}$")


def get_correlation_id() -> str | None:
    return _CORRELATION_ID_CONTEXT.get()


def set_correlation_id(value: str) -> Token[str | None]:
    return _CORRELATION_ID_CONTEXT.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _CORRELATION_ID_CONTEXT.reset(token)


def normalize_correlation_id(value: str | None) -> str | None:
    if value is None:
        return None

    candidate = value.strip()
    if not candidate:
        return None

    if _ALLOWED_CORRELATION_ID_PATTERN.fullmatch(candidate) is None:
        return None

    return candidate


def resolve_correlation_id(header_value: str | None) -> str:
    normalized = normalize_correlation_id(header_value)
    if normalized is not None:
        return normalized

    return uuid4().hex
