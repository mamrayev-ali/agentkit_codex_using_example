from datetime import datetime, timezone
from sqlite3 import Connection, IntegrityError, Row

from decider_api.domain.search_requests import (
    SearchRequest,
    SearchRequestDraft,
    normalize_request_status,
    validate_search_request_draft,
)


class SqliteSearchRequestRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def create(self, draft: SearchRequestDraft) -> SearchRequest:
        validated_draft = validate_search_request_draft(draft)
        created_at = datetime.now(timezone.utc).replace(microsecond=0)

        try:
            self._connection.execute(
                """
                INSERT INTO search_requests (
                    tenant_id,
                    request_id,
                    dossier_id,
                    query_text,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    validated_draft.tenant_id,
                    validated_draft.request_id,
                    validated_draft.dossier_id,
                    validated_draft.query_text,
                    validated_draft.status,
                    created_at.isoformat().replace("+00:00", "Z"),
                ),
            )
            self._connection.commit()
        except IntegrityError as exc:
            raise ValueError("Search request references unknown tenant dossier.") from exc

        return SearchRequest(
            tenant_id=validated_draft.tenant_id,
            request_id=validated_draft.request_id,
            dossier_id=validated_draft.dossier_id,
            query_text=validated_draft.query_text,
            status=validated_draft.status,
            created_at=created_at,
        )

    def get_by_id(self, *, tenant_id: str, request_id: str) -> SearchRequest | None:
        row = self._connection.execute(
            """
            SELECT
                tenant_id,
                request_id,
                dossier_id,
                query_text,
                status,
                created_at
            FROM search_requests
            WHERE tenant_id = ? AND request_id = ?
            """,
            (tenant_id, request_id),
        ).fetchone()

        if row is None:
            return None
        return _row_to_search_request(row)

    def list_for_tenant(self, *, tenant_id: str) -> list[SearchRequest]:
        rows = self._connection.execute(
            """
            SELECT
                tenant_id,
                request_id,
                dossier_id,
                query_text,
                status,
                created_at
            FROM search_requests
            WHERE tenant_id = ?
            ORDER BY created_at DESC, request_id DESC
            """,
            (tenant_id,),
        ).fetchall()
        return [_row_to_search_request(row) for row in rows]

    def update_status(
        self,
        *,
        tenant_id: str,
        request_id: str,
        status: str,
    ) -> SearchRequest | None:
        normalized_status = normalize_request_status(status)
        cursor = self._connection.execute(
            """
            UPDATE search_requests
            SET status = ?
            WHERE tenant_id = ? AND request_id = ?
            """,
            (normalized_status, tenant_id, request_id),
        )
        self._connection.commit()

        if cursor.rowcount == 0:
            return None
        return self.get_by_id(tenant_id=tenant_id, request_id=request_id)


def _row_to_search_request(row: Row) -> SearchRequest:
    created_at_raw = row["created_at"]
    if not isinstance(created_at_raw, str):
        raise ValueError("Invalid created_at value in search_requests row.")

    created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
    return SearchRequest(
        tenant_id=str(row["tenant_id"]),
        request_id=str(row["request_id"]),
        dossier_id=str(row["dossier_id"]),
        query_text=str(row["query_text"]),
        status=str(row["status"]),
        created_at=created_at,
    )
