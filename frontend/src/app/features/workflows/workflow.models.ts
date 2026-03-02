export type SubjectType = 'organization' | 'person';
export type SearchRequestStatus = 'queued' | 'running' | 'completed' | 'failed';

export interface DossierRecord {
  tenantId: string;
  dossierId: string;
  subjectName: string;
  subjectType: SubjectType;
  createdAt: string;
}

export interface SearchRequestRecord {
  tenantId: string;
  requestId: string;
  dossierId: string;
  queryText: string;
  status: SearchRequestStatus;
  createdAt: string;
}

export interface SearchRequestEnqueueMetadata {
  taskId: string;
  queueStatus: string;
  resultStatus: SearchRequestStatus | null;
}

export interface CreateDossierInput {
  subjectName: string;
  subjectType: SubjectType;
}

export interface CreateSearchRequestInput {
  dossierId: string;
  queryText: string;
  sourceKey: string;
  remoteUrl: string;
}

export interface ExportResult {
  tenantId: string;
  exportId: string;
  status: 'accepted';
  auditMetadata: {
    eventId: string;
    action: 'export.requested';
    actorSubject: string;
    tenantId: string;
    outcome: 'success' | 'forbidden';
    occurredAt: string;
    reason: string | null;
  };
}
