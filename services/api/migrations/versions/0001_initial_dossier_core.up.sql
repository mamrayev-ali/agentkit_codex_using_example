CREATE TABLE dossiers (
    tenant_id TEXT NOT NULL,
    dossier_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, dossier_id)
);

CREATE INDEX idx_dossiers_tenant_created
    ON dossiers (tenant_id, created_at);

CREATE TABLE search_requests (
    tenant_id TEXT NOT NULL,
    request_id TEXT NOT NULL,
    dossier_id TEXT NOT NULL,
    query_text TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, request_id),
    FOREIGN KEY (tenant_id, dossier_id)
        REFERENCES dossiers (tenant_id, dossier_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_search_requests_tenant_dossier
    ON search_requests (tenant_id, dossier_id);
