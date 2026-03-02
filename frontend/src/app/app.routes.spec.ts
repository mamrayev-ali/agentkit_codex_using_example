import '@angular/compiler';

import { adminGuard } from './auth/admin.guard';
import { anonymousGuard } from './auth/anonymous.guard';
import { authGuard } from './auth/auth.guard';
import { moduleGuard } from './auth/module.guard';
import { appRoutes } from './app.routes';

describe('appRoutes', () => {
  it('contains expected auth and shell route paths', () => {
    const paths = appRoutes.map((route) => route.path);

    expect(paths).toContain('');
    expect(paths).toContain('login');
    expect(paths).toContain('auth/callback');
    expect(paths).toContain('dashboard');
    expect(paths).toContain('dossiers');
    expect(paths).toContain('searches');
    expect(paths).toContain('exports');
    expect(paths).toContain('admin');
    expect(paths).toContain('watchlist');
    expect(paths).toContain('**');
  });

  it('redirects root path to dashboard', () => {
    const rootRoute = appRoutes.find((route) => route.path === '');

    expect(rootRoute?.redirectTo).toBe('dashboard');
    expect(rootRoute?.pathMatch).toBe('full');
  });

  it('protects shell routes and maps required module data', () => {
    const dashboardRoute = appRoutes.find((route) => route.path === 'dashboard');
    const dossiersRoute = appRoutes.find((route) => route.path === 'dossiers');
    const searchesRoute = appRoutes.find((route) => route.path === 'searches');
    const exportsRoute = appRoutes.find((route) => route.path === 'exports');
    const adminRoute = appRoutes.find((route) => route.path === 'admin');

    expect(dashboardRoute?.canActivate).toEqual([authGuard, moduleGuard]);
    expect(dashboardRoute?.data?.['requiredModule']).toBe('dashboard');

    expect(dossiersRoute?.canActivate).toEqual([authGuard, moduleGuard]);
    expect(dossiersRoute?.data?.['requiredModule']).toBe('dossiers');

    expect(searchesRoute?.canActivate).toEqual([authGuard, moduleGuard]);
    expect(searchesRoute?.data?.['requiredModule']).toBe('dossiers');

    expect(exportsRoute?.canActivate).toEqual([authGuard, moduleGuard]);
    expect(exportsRoute?.data?.['requiredModule']).toBe('dossiers');

    expect(adminRoute?.canActivate).toEqual([authGuard, adminGuard]);
  });

  it('uses anonymous guard for login and callback pages', () => {
    const loginRoute = appRoutes.find((route) => route.path === 'login');
    const callbackRoute = appRoutes.find((route) => route.path === 'auth/callback');

    expect(loginRoute?.canActivate).toEqual([anonymousGuard]);
    expect(callbackRoute?.canActivate).toEqual([anonymousGuard]);
  });
});
