import { appRoutes } from './app.routes';

describe('appRoutes', () => {
  it('contains expected shell route paths', () => {
    const paths = appRoutes.map((route) => route.path);

    expect(paths).toContain('');
    expect(paths).toContain('dashboard');
    expect(paths).toContain('dossiers');
    expect(paths).toContain('watchlist');
    expect(paths).toContain('**');
  });

  it('redirects root path to dashboard', () => {
    const rootRoute = appRoutes.find((route) => route.path === '');

    expect(rootRoute?.redirectTo).toBe('dashboard');
    expect(rootRoute?.pathMatch).toBe('full');
  });
});
