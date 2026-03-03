import { AuthService } from './auth.service';
import { type AuthContext, type AuthSession } from './auth.models';

class MemoryTokenStorage {
  session: AuthSession | null = null;
  pendingLogin: {
    state: string;
    codeVerifier: string;
    redirectTo: string;
    createdAt: number;
  } | null = null;

  readSession(): AuthSession | null {
    return this.session;
  }

  writeSession(session: AuthSession): void {
    this.session = session;
  }

  clearSession(): void {
    this.session = null;
  }

  readPendingLogin() {
    return this.pendingLogin;
  }

  writePendingLogin(request: {
    state: string;
    codeVerifier: string;
    redirectTo: string;
    createdAt: number;
  }): void {
    this.pendingLogin = request;
  }

  clearPendingLogin(): void {
    this.pendingLogin = null;
  }
}

class FakeAuthContextService {
  fetchResult: AuthContext = {
    authenticated: true,
    subject: 'analyst@acme.decider.local',
    tenantId: 'acme',
    roles: ['user'],
    scopes: ['read:data'],
    moduleEntitlements: ['dashboard'],
  };

  async fetchAuthContext(): Promise<AuthContext> {
    return this.fetchResult;
  }
}

function createAuthServiceForTest(dependencies?: {
  storage?: MemoryTokenStorage;
  authContext?: FakeAuthContextService;
}): {
  service: AuthService;
  storage: MemoryTokenStorage;
  authContext: FakeAuthContextService;
} {
  const storage = dependencies?.storage ?? new MemoryTokenStorage();
  const authContext = dependencies?.authContext ?? new FakeAuthContextService();

  const service = new AuthService(storage as never, authContext as never);
  return { service, storage, authContext };
}

describe('AuthService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('builds Authorization Code + PKCE login URL and stores pending login state', async () => {
    const { service, storage } = createAuthServiceForTest();

    const loginUrl = await service.beginLogin('/watchlist');
    const parsedUrl = new URL(loginUrl);

    expect(parsedUrl.pathname.endsWith('/protocol/openid-connect/auth')).toBe(true);
    expect(parsedUrl.searchParams.get('client_id')).toBe('decider-frontend');
    expect(parsedUrl.searchParams.get('response_type')).toBe('code');
    expect(parsedUrl.searchParams.get('scope')).toBe('openid');
    expect(parsedUrl.searchParams.get('code_challenge_method')).toBe('S256');
    expect(storage.pendingLogin?.redirectTo).toBe('/watchlist');
    expect(storage.pendingLogin?.state).toBe(parsedUrl.searchParams.get('state'));
  });

  it('includes login hint when requested', async () => {
    const { service } = createAuthServiceForTest();

    const loginUrl = await service.beginLogin('/dashboard', {
      loginHint: 'analyst@decider.invalid',
    });
    const parsedUrl = new URL(loginUrl);

    expect(parsedUrl.searchParams.get('login_hint')).toBe('analyst@decider.invalid');
  });

  it('completes callback, stores session, and loads backend auth context', async () => {
    const { service } = createAuthServiceForTest();

    const loginUrl = await service.beginLogin('/dossiers');
    const state = new URL(loginUrl).searchParams.get('state');

    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            access_token: 'token-value',
            token_type: 'Bearer',
            expires_in: 3600,
            id_token: 'id-token',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      ),
    );

    const result = await service.completeLoginFromCallback(
      new URLSearchParams({
        code: 'code-value',
        state: state ?? '',
      }),
    );

    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.redirectTo).toBe('/dossiers');
    }

    expect(service.isAuthenticated()).toBe(true);
    expect(service.hasModule('dashboard')).toBe(true);
    expect(service.accessToken()).toBe('token-value');
    expect(service.tenantId()).toBe('acme');
    expect(service.subject()).toBe('analyst@acme.decider.local');
    expect(service.hasScope('read:data')).toBe(true);
  });

  it('detects admin actor from roles or entitlement scopes', async () => {
    const authContext = new FakeAuthContextService();
    authContext.fetchResult = {
      authenticated: true,
      subject: 'admin-user',
      tenantId: 'acme',
      roles: ['admin'],
      scopes: ['read:data', 'entitlements:write'],
      moduleEntitlements: ['dashboard'],
    };
    const { service } = createAuthServiceForTest({ authContext });

    const loginUrl = await service.beginLogin('/dashboard');
    const state = new URL(loginUrl).searchParams.get('state');

    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            access_token: 'token-value',
            token_type: 'Bearer',
            expires_in: 3600,
            id_token: 'id-token',
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      ),
    );

    await service.completeLoginFromCallback(
      new URLSearchParams({
        code: 'code-value',
        state: state ?? '',
      }),
    );

    expect(service.isAdminActor()).toBe(true);
  });

  it('rejects callback when state does not match pending login', async () => {
    const { service, storage } = createAuthServiceForTest();

    await service.beginLogin('/dashboard');

    const result = await service.completeLoginFromCallback(
      new URLSearchParams({
        code: 'code-value',
        state: 'unexpected-state',
      }),
    );

    expect(result.ok).toBe(false);
    expect(storage.pendingLogin).toBeNull();
  });

  it('treats expired session as unauthenticated and requires re-login', async () => {
    const storage = new MemoryTokenStorage();
    storage.session = {
      accessToken: 'expired-token',
      tokenType: 'Bearer',
      idToken: null,
      refreshToken: null,
      expiresAt: Date.now() - 60_000,
    };

    const { service } = createAuthServiceForTest({ storage });

    const isAuthenticated = await service.ensureAuthenticated();
    expect(isAuthenticated).toBe(false);
    expect(service.accessToken()).toBeNull();

    const loginUrl = await service.beginLogin('/dashboard');
    expect(loginUrl).toContain('/protocol/openid-connect/auth');
  });

  it('preserves pending login state during service initialization without a session', () => {
    const storage = new MemoryTokenStorage();
    storage.pendingLogin = {
      state: 'callback-state',
      codeVerifier: 'code-verifier',
      redirectTo: '/dashboard',
      createdAt: Date.now(),
    };

    createAuthServiceForTest({ storage });

    expect(storage.pendingLogin).toEqual({
      state: 'callback-state',
      codeVerifier: 'code-verifier',
      redirectTo: '/dashboard',
      createdAt: storage.pendingLogin?.createdAt,
    });
  });
});
