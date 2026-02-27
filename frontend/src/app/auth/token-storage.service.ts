import { Injectable } from '@angular/core';

import { type AuthSession, type PendingLoginRequest } from './auth.models';

const _SESSION_KEY = 'decider.auth.session.v1';
const _PENDING_LOGIN_KEY = 'decider.auth.pending-login.v1';

function parseStoredJson<T>(value: string | null): T | null {
  if (value === null) {
    return null;
  }

  try {
    const parsed: unknown = JSON.parse(value);
    return parsed as T;
  } catch {
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class TokenStorageService {
  readSession(): AuthSession | null {
    return parseStoredJson<AuthSession>(sessionStorage.getItem(_SESSION_KEY));
  }

  writeSession(session: AuthSession): void {
    sessionStorage.setItem(_SESSION_KEY, JSON.stringify(session));
  }

  clearSession(): void {
    sessionStorage.removeItem(_SESSION_KEY);
  }

  readPendingLogin(): PendingLoginRequest | null {
    return parseStoredJson<PendingLoginRequest>(sessionStorage.getItem(_PENDING_LOGIN_KEY));
  }

  writePendingLogin(request: PendingLoginRequest): void {
    sessionStorage.setItem(_PENDING_LOGIN_KEY, JSON.stringify(request));
  }

  clearPendingLogin(): void {
    sessionStorage.removeItem(_PENDING_LOGIN_KEY);
  }
}
