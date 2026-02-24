import { environment } from './environment';

describe('environment', () => {
  it('exposes non-production defaults for local development', () => {
    expect(environment.production).toBe(false);
    expect(environment.name).toBe('development');
    expect(environment.apiBaseUrl).toContain('/api/v1');
  });
});
