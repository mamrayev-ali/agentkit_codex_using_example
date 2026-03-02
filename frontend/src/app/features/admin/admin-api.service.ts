import { Inject, Injectable } from '@angular/core';

import { environment } from '../../../environments/environment';
import { AuthService } from '../../auth/auth.service';
import type {
  AuditEventAction,
  AuditEventOutcome,
  AuditEventRecord,
  SubjectEntitlements,
  SupportedModule,
} from './admin.models';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function readString(value: unknown, fieldName: string): string {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`Admin payload field "${fieldName}" must be a non-empty string.`);
  }

  return value.trim();
}

function readNullableString(value: unknown, fieldName: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  return readString(value, fieldName);
}

function readAction(value: unknown): AuditEventAction {
  const action = readString(value, 'action');
  if (action !== 'entitlements.updated' && action !== 'export.requested') {
    throw new Error(`Unsupported audit action "${action}".`);
  }

  return action;
}

function readOutcome(value: unknown): AuditEventOutcome {
  const outcome = readString(value, 'outcome');
  if (outcome !== 'success' && outcome !== 'forbidden') {
    throw new Error(`Unsupported audit outcome "${outcome}".`);
  }

  return outcome;
}

function readModules(value: unknown): SupportedModule[] {
  if (!Array.isArray(value)) {
    throw new Error('Admin payload field "enabled_modules" must be an array.');
  }

  const modules: SupportedModule[] = [];
  for (const entry of value) {
    const moduleKey = readString(entry, 'enabled_modules');
    if (moduleKey !== 'dashboard' && moduleKey !== 'dossiers' && moduleKey !== 'watchlist') {
      throw new Error(`Unsupported module "${moduleKey}".`);
    }

    if (!modules.includes(moduleKey)) {
      modules.push(moduleKey);
    }
  }

  return modules;
}

export class AdminApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'AdminApiError';
  }
}

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  constructor(@Inject(AuthService) private readonly authService: AuthService) {}

  async getEntitlements(subject: string): Promise<SubjectEntitlements> {
    const payload = await this.requestJson<unknown>(
      'GET',
      this.resolveTenantPath(`/entitlements/${encodeURIComponent(subject.trim())}`),
    );

    return this.normalizeEntitlements(payload);
  }

  async updateEntitlements(
    subject: string,
    enabledModules: SupportedModule[],
  ): Promise<SubjectEntitlements> {
    const payload = await this.requestJson<unknown>(
      'PUT',
      this.resolveTenantPath(`/entitlements/${encodeURIComponent(subject.trim())}`),
      {
        enabled_modules: enabledModules,
      },
    );

    return this.normalizeEntitlements(payload);
  }

  async listAuditEvents(): Promise<AuditEventRecord[]> {
    const payload = await this.requestJson<unknown>('GET', this.resolveTenantPath('/audit/events'));
    if (!isRecord(payload) || !Array.isArray(payload['events'])) {
      throw new Error('Audit event payload has invalid shape.');
    }

    return payload['events'].map((item) => this.normalizeAuditEvent(item));
  }

  private normalizeEntitlements(value: unknown): SubjectEntitlements {
    if (!isRecord(value)) {
      throw new Error('Entitlements payload has invalid shape.');
    }

    const auditMetadata = value['audit_metadata'];
    return {
      tenantId: readString(value['tenant_id'], 'tenant_id'),
      subject: readString(value['subject'], 'subject'),
      enabledModules: readModules(value['enabled_modules']),
      auditMetadata:
        auditMetadata === null || auditMetadata === undefined
          ? null
          : {
              eventId: readString(
                isRecord(auditMetadata) ? auditMetadata['event_id'] : null,
                'audit_metadata.event_id',
              ),
              action: 'entitlements.updated',
              actorSubject: readString(
                isRecord(auditMetadata) ? auditMetadata['actor_subject'] : null,
                'audit_metadata.actor_subject',
              ),
              targetSubject: readString(
                isRecord(auditMetadata) ? auditMetadata['target_subject'] : null,
                'audit_metadata.target_subject',
              ),
              tenantId: readString(
                isRecord(auditMetadata) ? auditMetadata['tenant_id'] : null,
                'audit_metadata.tenant_id',
              ),
              occurredAt: readString(
                isRecord(auditMetadata) ? auditMetadata['occurred_at'] : null,
                'audit_metadata.occurred_at',
              ),
            },
    };
  }

  private normalizeAuditEvent(value: unknown): AuditEventRecord {
    if (!isRecord(value)) {
      throw new Error('Audit event entry has invalid shape.');
    }

    return {
      eventId: readString(value['event_id'], 'event_id'),
      action: readAction(value['action']),
      actorSubject: readString(value['actor_subject'], 'actor_subject'),
      targetSubject: readNullableString(value['target_subject'], 'target_subject'),
      tenantId: readString(value['tenant_id'], 'tenant_id'),
      outcome: readOutcome(value['outcome']),
      occurredAt: readString(value['occurred_at'], 'occurred_at'),
      reason: readNullableString(value['reason'], 'reason'),
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
    method: 'GET' | 'PUT',
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
      let message = `Admin request failed with status ${response.status}.`;
      try {
        const payload: unknown = await response.json();
        if (isRecord(payload) && typeof payload['detail'] === 'string' && payload['detail'].trim()) {
          message = payload['detail'];
        }
      } catch {
        // Keep generic message when the response body is not JSON.
      }

      throw new AdminApiError(message, response.status);
    }

    return (await response.json()) as TResponse;
  }
}
