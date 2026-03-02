import { Inject, Injectable } from '@angular/core';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../auth/auth.service';
import type {
  CreateDossierInput,
  CreateSearchRequestInput,
  DossierRecord,
  ExportResult,
  SearchRequestEnqueueMetadata,
  SearchRequestRecord,
  SearchRequestStatus,
} from './workflow.models';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function readString(value: unknown, fieldName: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`Workflow payload field "${fieldName}" must be a non-empty string.`);
  }

  return value.trim();
}

function readNullableStatus(value: unknown): SearchRequestStatus | null {
  if (value === null || value === undefined) {
    return null;
  }

  return readStatus(value);
}

function readStatus(value: unknown): SearchRequestStatus {
  const normalized = readString(value, 'status');
  if (
    normalized !== 'queued' &&
    normalized !== 'running' &&
    normalized !== 'completed' &&
    normalized !== 'failed'
  ) {
    throw new Error(`Unsupported search status "${normalized}".`);
  }

  return normalized;
}

export class WorkflowApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'WorkflowApiError';
  }
}

@Injectable({ providedIn: 'root' })
export class WorkflowApiService {
  constructor(@Inject(AuthService) private readonly authService: AuthService) {}

  async listDossiers(): Promise<DossierRecord[]> {
    const payload = await this.requestJson<unknown>('GET', this.resolveTenantPath('/dossiers'));
    if (!isRecord(payload) || !Array.isArray(payload['dossiers'])) {
      throw new Error('Dossier list payload has invalid shape.');
    }

    return payload['dossiers'].map((item) => this.normalizeDossier(item));
  }

  async createDossier(input: CreateDossierInput): Promise<DossierRecord> {
    const payload = await this.requestJson<unknown>('POST', this.resolveTenantPath('/dossiers'), {
      subject_name: input.subjectName,
      subject_type: input.subjectType,
    });

    return this.normalizeDossier(payload);
  }

  async listSearchRequests(): Promise<SearchRequestRecord[]> {
    const payload = await this.requestJson<unknown>('GET', this.resolveTenantPath('/search-requests'));
    if (!isRecord(payload) || !Array.isArray(payload['search_requests'])) {
      throw new Error('Search request list payload has invalid shape.');
    }

    return payload['search_requests'].map((item) => this.normalizeSearchRequest(item));
  }

  async getSearchStatus(requestId: string): Promise<SearchRequestStatus> {
    const payload = await this.requestJson<unknown>(
      'GET',
      this.resolveTenantPath(`/search-requests/${encodeURIComponent(requestId)}/status`),
    );

    if (!isRecord(payload)) {
      throw new Error('Search status payload has invalid shape.');
    }

    return readStatus(payload['status']);
  }

  async createSearchRequest(input: CreateSearchRequestInput): Promise<{
    searchRequest: SearchRequestRecord;
    enqueueMetadata: SearchRequestEnqueueMetadata;
  }> {
    const payload = await this.requestJson<unknown>(
      'POST',
      this.resolveTenantPath('/search-requests'),
      {
        dossier_id: input.dossierId,
        query_text: input.queryText,
        source_key: input.sourceKey,
        remote_url: input.remoteUrl,
      },
    );

    if (!isRecord(payload)) {
      throw new Error('Search create payload has invalid shape.');
    }

    return {
      searchRequest: this.normalizeSearchRequest(payload['search_request']),
      enqueueMetadata: this.normalizeEnqueueMetadata(payload['enqueue_metadata']),
    };
  }

  async requestExport(): Promise<ExportResult> {
    const payload = await this.requestJson<unknown>('POST', this.resolveTenantPath('/exports'));
    if (!isRecord(payload) || !isRecord(payload['audit_metadata'])) {
      throw new Error('Export payload has invalid shape.');
    }

    const auditMetadata = payload['audit_metadata'];
    return {
      tenantId: readString(payload['tenant_id'], 'tenant_id'),
      exportId: readString(payload['export_id'], 'export_id'),
      status: 'accepted',
      auditMetadata: {
        eventId: readString(auditMetadata['event_id'], 'audit_metadata.event_id'),
        action: 'export.requested',
        actorSubject: readString(auditMetadata['actor_subject'], 'audit_metadata.actor_subject'),
        tenantId: readString(auditMetadata['tenant_id'], 'audit_metadata.tenant_id'),
        outcome:
          readString(auditMetadata['outcome'], 'audit_metadata.outcome') === 'forbidden'
            ? 'forbidden'
            : 'success',
        occurredAt: readString(auditMetadata['occurred_at'], 'audit_metadata.occurred_at'),
        reason:
          typeof auditMetadata['reason'] === 'string' && auditMetadata['reason'].trim()
            ? auditMetadata['reason']
            : null,
      },
    };
  }

  private normalizeDossier(value: unknown): DossierRecord {
    if (!isRecord(value)) {
      throw new Error('Dossier payload has invalid shape.');
    }

    return {
      tenantId: readString(value['tenant_id'], 'tenant_id'),
      dossierId: readString(value['dossier_id'], 'dossier_id'),
      subjectName: readString(value['subject_name'], 'subject_name'),
      subjectType: readString(value['subject_type'], 'subject_type') as DossierRecord['subjectType'],
      createdAt: readString(value['created_at'], 'created_at'),
    };
  }

  private normalizeSearchRequest(value: unknown): SearchRequestRecord {
    if (!isRecord(value)) {
      throw new Error('Search request payload has invalid shape.');
    }

    return {
      tenantId: readString(value['tenant_id'], 'tenant_id'),
      requestId: readString(value['request_id'], 'request_id'),
      dossierId: readString(value['dossier_id'], 'dossier_id'),
      queryText: readString(value['query_text'], 'query_text'),
      status: readStatus(value['status']),
      createdAt: readString(value['created_at'], 'created_at'),
    };
  }

  private normalizeEnqueueMetadata(value: unknown): SearchRequestEnqueueMetadata {
    if (!isRecord(value)) {
      throw new Error('Enqueue metadata payload has invalid shape.');
    }

    return {
      taskId: readString(value['task_id'], 'task_id'),
      queueStatus: readString(value['queue_status'], 'queue_status'),
      resultStatus: readNullableStatus(value['result_status']),
    };
  }

  private resolveTenantPath(path: string): string {
    const tenantId = this.authService.tenantId();
    if (tenantId === null) {
      throw new Error('Tenant context is missing.');
    }

    return `${environment.apiBaseUrl}/tenants/${encodeURIComponent(tenantId)}${path}`;
  }

  private async requestJson<TResponse>(
    method: 'GET' | 'POST',
    url: string,
    body?: Record<string, unknown>,
  ): Promise<TResponse> {
    const accessToken = this.authService.accessToken();
    if (accessToken === null) {
      throw new Error('Access token is unavailable.');
    }

    const response = await fetch(url, {
      method,
      headers: {
        Authorization: `Bearer ${accessToken}`,
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });

    if (!response.ok) {
      let message = `Workflow request failed with status ${response.status}.`;
      try {
        const payload: unknown = await response.json();
        if (isRecord(payload) && typeof payload['detail'] === 'string' && payload['detail'].trim()) {
          message = payload['detail'];
        }
      } catch {
        // Ignore body parsing errors and keep the generic error message.
      }

      throw new WorkflowApiError(message, response.status);
    }

    return (await response.json()) as TResponse;
  }
}
