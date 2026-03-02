import { Inject, Injectable, computed, signal } from '@angular/core';

import { environment } from '../../environments/environment';
import type {
  AuthCallbackResult,
  AuthContext,
  AuthSession,
  OidcTokenPayload,
  PendingLoginRequest,
} from './auth.models';
import { AuthContextRequestError, AuthContextService } from './auth-context.service';
import { createPkceMaterial } from './pkce';
import { TokenStorageService } from './token-storage.service';

const _CLOCK_SKEW_MS = 15_000;
const _DASHBOARD_ROUTE = '/dashboard';

function normalizeRoutePath(candidate: string): string {
  if (!candidate) {
    return _DASHBOARD_ROUTE;
  }

  if (candidate.startsWith('/')) {
    return candidate;
  }

  return _DASHBOARD_ROUTE;
}

function readTokenExpiryMs(payload: OidcTokenPayload): number {
  if (typeof payload.expires_in === 'number' && Number.isFinite(payload.expires_in)) {
    return Math.max(0, payload.expires_in * 1000);
  }

  return 0;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly _session = signal<AuthSession | null>(null);
  private readonly _authContext = signal<AuthContext | null>(null);

  readonly authContext = this._authContext.asReadonly();
  readonly moduleEntitlements = computed(() => {
    const authContext = this._authContext();
    return authContext === null ? [] : authContext.moduleEntitlements;
  });

  constructor(
    @Inject(TokenStorageService) private readonly storage: TokenStorageService,
    @Inject(AuthContextService) private readonly authContextService: AuthContextService,
  ) {
    this._session.set(this.storage.readSession());
    void this.initialize();
  }

  isAuthenticated(): boolean {
    const session = this.readValidSession();
    return session !== null && this._authContext() !== null;
  }

  accessToken(): string | null {
    return this.readValidSession()?.accessToken ?? null;
  }

  tenantId(): string | null {
    return this._authContext()?.tenantId ?? null;
  }

  subject(): string | null {
    return this._authContext()?.subject ?? null;
  }

  hasModule(moduleKey: string): boolean {
    const normalizedModule = moduleKey.trim().toLowerCase();
    return this.moduleEntitlements().includes(normalizedModule);
  }

  hasScope(scopeKey: string): boolean {
    const normalizedScope = scopeKey.trim().toLowerCase();
    const authContext = this._authContext();
    if (authContext === null || !normalizedScope) {
      return false;
    }

    return authContext.scopes.includes(normalizedScope);
  }

  isAdminActor(): boolean {
    const authContext = this._authContext();
    if (authContext === null) {
      return false;
    }

    return (
      authContext.roles.includes('admin') ||
      authContext.scopes.includes('entitlements:write') ||
      authContext.scopes.includes('entitlements:admin')
    );
  }

  async beginLogin(redirectTo: string): Promise<string> {
    const normalizedRedirect = normalizeRoutePath(redirectTo);
    const pkce = await createPkceMaterial();

    const pendingLogin: PendingLoginRequest = {
      state: pkce.state,
      codeVerifier: pkce.codeVerifier,
      redirectTo: normalizedRedirect,
      createdAt: Date.now(),
    };

    this.storage.writePendingLogin(pendingLogin);

    const params = new URLSearchParams({
      client_id: environment.oidc.clientId,
      redirect_uri: this.buildAbsolutePath(environment.oidc.redirectPath),
      response_type: 'code',
      scope: environment.oidc.scopes,
      state: pkce.state,
      code_challenge: pkce.codeChallenge,
      code_challenge_method: 'S256',
    });

    return `${this.resolveOidcEndpoint('auth')}?${params.toString()}`;
  }

  async completeLoginFromCallback(params: URLSearchParams): Promise<AuthCallbackResult> {
    const callbackError = params.get('error');
    if (callbackError !== null) {
      const description = params.get('error_description') ?? 'Authentication failed.';
      return { ok: false, message: `${callbackError}: ${description}` };
    }

    const code = params.get('code');
    const state = params.get('state');
    if (code === null || state === null) {
      return { ok: false, message: 'Missing OIDC callback parameters.' };
    }

    const pendingLogin = this.storage.readPendingLogin();
    if (pendingLogin === null) {
      return { ok: false, message: 'Login session is missing. Start sign-in again.' };
    }

    if (pendingLogin.state !== state) {
      this.storage.clearPendingLogin();
      return { ok: false, message: 'Login state validation failed.' };
    }

    try {
      const tokenPayload = await this.exchangeAuthorizationCode(code, pendingLogin.codeVerifier);
      this.commitSession(tokenPayload);
      this.storage.clearPendingLogin();

      const authContext = await this.refreshAuthContext();
      if (authContext === null) {
        this.clearSession();
        return {
          ok: false,
          message: 'Authenticated session was rejected by backend auth context.',
        };
      }

      return {
        ok: true,
        redirectTo: normalizeRoutePath(pendingLogin.redirectTo),
      };
    } catch {
      this.clearSession();
      return {
        ok: false,
        message: 'Failed to complete login. Try again.',
      };
    }
  }

  async ensureAuthenticated(): Promise<boolean> {
    if (this.readValidSession() === null) {
      this.clearRuntimeSession();
      return false;
    }

    if (this._authContext() !== null) {
      return true;
    }

    const authContext = await this.refreshAuthContext();
    return authContext !== null;
  }

  async refreshAuthContext(): Promise<AuthContext | null> {
    const session = this.readValidSession();
    if (session === null) {
      this.clearRuntimeSession();
      return null;
    }

    try {
      const authContext = await this.authContextService.fetchAuthContext(session.accessToken);
      this._authContext.set(authContext);
      return authContext;
    } catch (error) {
      if (error instanceof AuthContextRequestError && error.status === 401) {
        this.clearRuntimeSession();
        return null;
      }

      this._authContext.set(null);
      return null;
    }
  }

  createLogoutUrl(): string {
    const params = new URLSearchParams({
      client_id: environment.oidc.clientId,
      post_logout_redirect_uri: this.buildAbsolutePath(
        environment.oidc.postLogoutRedirectPath,
      ),
    });

    const session = this.readValidSession();
    if (session?.idToken) {
      params.set('id_token_hint', session.idToken);
    }

    return `${this.resolveOidcEndpoint('logout')}?${params.toString()}`;
  }

  clearSession(): void {
    this.clearRuntimeSession();
    this.storage.clearPendingLogin();
  }

  private clearRuntimeSession(): void {
    this._session.set(null);
    this._authContext.set(null);
    this.storage.clearSession();
  }

  private async initialize(): Promise<void> {
    if (this.readValidSession() === null) {
      this.clearRuntimeSession();
      return;
    }

    await this.refreshAuthContext();
  }

  private readValidSession(): AuthSession | null {
    const session = this._session();
    if (session === null) {
      return null;
    }

    if (Date.now() + _CLOCK_SKEW_MS >= session.expiresAt) {
      return null;
    }

    return session;
  }

  private commitSession(payload: OidcTokenPayload): void {
    if (typeof payload.access_token !== 'string' || !payload.access_token.trim()) {
      throw new Error('OIDC token response is missing access_token.');
    }

    const expiresInMs = readTokenExpiryMs(payload);

    const session: AuthSession = {
      accessToken: payload.access_token,
      tokenType:
        typeof payload.token_type === 'string' && payload.token_type.trim()
          ? payload.token_type
          : 'Bearer',
      idToken: typeof payload.id_token === 'string' ? payload.id_token : null,
      refreshToken: typeof payload.refresh_token === 'string' ? payload.refresh_token : null,
      expiresAt: Date.now() + Math.max(expiresInMs, 60_000),
    };

    this._session.set(session);
    this.storage.writeSession(session);
  }

  private async exchangeAuthorizationCode(
    code: string,
    codeVerifier: string,
  ): Promise<OidcTokenPayload> {
    const body = new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      client_id: environment.oidc.clientId,
      redirect_uri: this.buildAbsolutePath(environment.oidc.redirectPath),
      code_verifier: codeVerifier,
    });

    const response = await fetch(this.resolveOidcEndpoint('token'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    });

    if (!response.ok) {
      throw new Error(`OIDC token exchange failed with status ${response.status}.`);
    }

    const payload: unknown = await response.json();
    if (typeof payload !== 'object' || payload === null) {
      throw new Error('OIDC token payload has invalid shape.');
    }

    return payload as OidcTokenPayload;
  }

  private resolveOidcEndpoint(endpoint: 'auth' | 'token' | 'logout'): string {
    const issuer = environment.oidc.issuerUrl.replace(/\/$/, '');

    return `${issuer}/protocol/openid-connect/${endpoint}`;
  }

  private buildAbsolutePath(path: string): string {
    const origin = window.location.origin;
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${origin}${normalizedPath}`;
  }
}
