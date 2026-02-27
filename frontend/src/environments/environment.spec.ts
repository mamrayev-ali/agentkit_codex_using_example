import { environment } from './environment';

describe('environment', () => {
  it('exposes non-production defaults for local development', () => {
    expect(environment.production).toBe(false);
    expect(environment.name).toBe('development');
    expect(environment.apiBaseUrl).toContain('/api/v1');
  });

  it('includes OIDC settings for Authorization Code + PKCE flow', () => {
    expect(environment.oidc.clientId).toBe('decider-frontend');
    expect(environment.oidc.issuerUrl).toContain('/realms/decider-local');
    expect(environment.oidc.redirectPath).toBe('/auth/callback');
  });
});
