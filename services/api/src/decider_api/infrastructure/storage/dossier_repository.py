from datetime import datetime, timezone
from sqlite3 import Connection, Row

from decider_api.domain.dossiers import (
    Dossier,
    DossierDraft,
    validate_dossier_draft,
)


class SqliteDossierRepository:
    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    def create(self, draft: DossierDraft) -> Dossier:
        validated_draft = validate_dossier_draft(draft)
        created_at = datetime.now(timezone.utc).replace(microsecond=0)

        self._connection.execute(
            """
            INSERT INTO dossiers (
                tenant_id,
                dossier_id,
                subject_name,
                subject_type,
                created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                validated_draft.tenant_id,
                validated_draft.dossier_id,
                validated_draft.subject_name,
                validated_draft.subject_type,
                created_at.isoformat().replace("+00:00", "Z"),
            ),
        )
        self._connection.commit()

        return Dossier(
            tenant_id=validated_draft.tenant_id,
            dossier_id=validated_draft.dossier_id,
            subject_name=validated_draft.subject_name,
            subject_type=validated_draft.subject_type,
            created_at=created_at,
        )

    def get_by_id(self, *, tenant_id: str, dossier_id: str) -> Dossier | None:
        row = self._connection.execute(
            """
            SELECT
                tenant_id,
                dossier_id,
                subject_name,
                subject_type,
                created_at
            FROM dossiers
            WHERE tenant_id = ? AND dossier_id = ?
            """,
            (tenant_id, dossier_id),
        ).fetchone()

        if row is None:
            return None
        return _row_to_dossier(row)


def _row_to_dossier(row: Row) -> Dossier:
    created_at_raw = row["created_at"]
    if not isinstance(created_at_raw, str):
        raise ValueError("Invalid created_at value in dossiers row.")

    created_at = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))
    return Dossier(
        tenant_id=str(row["tenant_id"]),
        dossier_id=str(row["dossier_id"]),
        subject_name=str(row["subject_name"]),
        subject_type=str(row["subject_type"]),
        created_at=created_at,
    )
