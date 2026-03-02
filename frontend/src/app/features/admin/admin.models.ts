export type SupportedModule = 'dashboard' | 'dossiers' | 'watchlist';
export type AuditEventAction = 'entitlements.updated' | 'export.requested';
export type AuditEventOutcome = 'success' | 'forbidden';

export interface EntitlementAuditMetadata {
  eventId: string;
  action: 'entitlements.updated';
  actorSubject: string;
  targetSubject: string;
  tenantId: string;
  occurredAt: string;
}

export interface SubjectEntitlements {
  tenantId: string;
  subject: string;
  enabledModules: SupportedModule[];
  auditMetadata: EntitlementAuditMetadata | null;
}

export interface AuditEventRecord {
  eventId: string;
  action: AuditEventAction;
  actorSubject: string;
  targetSubject: string | null;
  tenantId: string;
  outcome: AuditEventOutcome;
  occurredAt: string;
  reason: string | null;
}
