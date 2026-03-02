CREATE TABLE IF NOT EXISTS managed_entitlements (
    tenant_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    enabled_modules TEXT NOT NULL,
    updated_by_subject TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tenant_id, subject)
);

CREATE INDEX IF NOT EXISTS idx_managed_entitlements_tenant
    ON managed_entitlements (tenant_id);

CREATE TABLE IF NOT EXISTS audit_events (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    actor_subject TEXT NOT NULL,
    target_subject TEXT,
    tenant_id TEXT NOT NULL,
    outcome TEXT NOT NULL,
    reason TEXT,
    occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_tenant_occurred
    ON audit_events (tenant_id, occurred_at DESC, audit_id DESC);
