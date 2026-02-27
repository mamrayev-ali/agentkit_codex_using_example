import { Injectable } from '@angular/core';

import { environment } from '../../environments/environment';
import { type AuthContext } from './auth.models';

const _DASHBOARD_MODULE = 'dashboard';

function normalizeStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const normalized: string[] = [];
  for (const entry of value) {
    if (typeof entry !== 'string') {
      continue;
    }

    const trimmed = entry.trim().toLowerCase();
    if (!trimmed || normalized.includes(trimmed)) {
      continue;
    }

    normalized.push(trimmed);
  }

  return normalized;
}

export class AuthContextRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'AuthContextRequestError';
  }
}

@Injectable({ providedIn: 'root' })
export class AuthContextService {
  async fetchAuthContext(accessToken: string): Promise<AuthContext> {
    const response = await fetch(`${environment.apiBaseUrl}/auth/context`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new AuthContextRequestError('Unable to fetch auth context.', response.status);
    }

    const payload: unknown = await response.json();
    return this.normalizeAuthContext(payload);
  }

  private normalizeAuthContext(value: unknown): AuthContext {
    if (typeof value !== 'object' || value === null) {
      throw new Error('Auth context payload has invalid shape.');
    }

    const record = value as Record<string, unknown>;

    if (record['authenticated'] !== true) {
      throw new Error('Auth context payload is not authenticated.');
    }

    const subject = this.readRequiredString(record['subject'], 'subject');
    const tenantId = this.readRequiredString(record['tenant_id'], 'tenant_id');

    const moduleEntitlements = normalizeStringArray(record['module_entitlements']);

    return {
      authenticated: true,
      subject,
      tenantId,
      roles: normalizeStringArray(record['roles']),
      scopes: normalizeStringArray(record['scopes']),
      moduleEntitlements:
        moduleEntitlements.length > 0 ? moduleEntitlements : [_DASHBOARD_MODULE],
    };
  }

  private readRequiredString(value: unknown, fieldName: string): string {
    if (typeof value !== 'string') {
      throw new Error(`Auth context field "${fieldName}" must be a string.`);
    }

    const normalized = value.trim();
    if (!normalized) {
      throw new Error(`Auth context field "${fieldName}" must not be empty.`);
    }

    return normalized;
  }
}
