import '@angular/compiler';

import { AppComponent } from './app.component';
import { type AuthContext } from './auth/auth.models';

class FakeAuthService {
  private authenticatedValue = false;
  private modulesValue: string[] = [];
  private contextValue: AuthContext | null = null;

  logoutCalled = false;

  authContext(): AuthContext | null {
    return this.contextValue;
  }

  isAuthenticated(): boolean {
    return this.authenticatedValue;
  }

  hasModule(moduleKey: string): boolean {
    return this.modulesValue.includes(moduleKey);
  }

  createLogoutUrl(): string {
    return 'http://localhost:8080/realms/decider-local/protocol/openid-connect/logout';
  }

  clearSession(): void {
    this.logoutCalled = true;
  }

  setState(next: { authenticated: boolean; modules: string[]; context: AuthContext | null }): void {
    this.authenticatedValue = next.authenticated;
    this.modulesValue = next.modules;
    this.contextValue = next.context;
  }
}

describe('AppComponent', () => {
  it('exposes shell title and environment label', () => {
    const fakeAuthService = new FakeAuthService();
    const app = new AppComponent(fakeAuthService as never);

    expect(app.appName).toBe('Decider');
    expect(app.environmentName).toBe('development');
  });

  it('reflects authenticated state and module visibility from auth service', () => {
    const fakeAuthService = new FakeAuthService();
    fakeAuthService.setState({
      authenticated: true,
      modules: ['dashboard', 'watchlist'],
      context: {
        authenticated: true,
        subject: 'demo-user',
        tenantId: 'acme',
        roles: ['user'],
        scopes: ['read:data'],
        moduleEntitlements: ['dashboard', 'watchlist'],
      },
    });

    const app = new AppComponent(fakeAuthService as never);

    expect(app.isAuthenticated()).toBe(true);
    expect(app.isModuleVisible('dashboard')).toBe(true);
    expect(app.isModuleVisible('watchlist')).toBe(true);
    expect(app.isModuleVisible('dossiers')).toBe(false);
    expect(app.authContext()?.tenantId).toBe('acme');
  });
});
