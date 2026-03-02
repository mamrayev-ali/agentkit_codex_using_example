import { TokenStorageService } from './token-storage.service';

describe('TokenStorageService', () => {
  beforeEach(() => {
    sessionStorage.clear();
    localStorage.clear();
  });

  it('stores auth session in sessionStorage only', () => {
    const storage = new TokenStorageService();

    storage.writeSession({
      accessToken: 'access-token',
      tokenType: 'Bearer',
      idToken: 'id-token',
      refreshToken: null,
      expiresAt: 123_456,
    });

    expect(sessionStorage.getItem('decider.auth.session.v1')).toContain('access-token');
    expect(localStorage.getItem('decider.auth.session.v1')).toBeNull();
  });

  it('stores pending login in localStorage so redirect state survives callback', () => {
    const storage = new TokenStorageService();

    storage.writePendingLogin({
      state: 'state-123',
      codeVerifier: 'verifier-123',
      redirectTo: '/dashboard',
      createdAt: 123_456,
    });

    sessionStorage.clear();

    expect(storage.readPendingLogin()).toEqual({
      state: 'state-123',
      codeVerifier: 'verifier-123',
      redirectTo: '/dashboard',
      createdAt: 123_456,
    });
  });
});
