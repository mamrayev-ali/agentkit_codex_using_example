import '@angular/compiler';

import { createEnvironmentInjector, runInInjectionContext, type Provider } from '@angular/core';
import { Router, type RouterStateSnapshot } from '@angular/router';

import { adminGuard } from './admin.guard';
import { anonymousGuard } from './anonymous.guard';
import { AuthService } from './auth.service';
import { authGuard } from './auth.guard';
import { moduleGuard } from './module.guard';

describe('auth guards', () => {
  const authServiceMock = {
    ensureAuthenticated: vi.fn<() => Promise<boolean>>(),
    hasModule: vi.fn<(moduleKey: string) => boolean>(),
    isAdminActor: vi.fn<() => boolean>(),
  };
  const routerMock = {
    createUrlTree: vi.fn(
      (commands: unknown[], extras?: { queryParams?: Record<string, string> }) => ({
        commands,
        extras,
      }),
    ),
  };

  beforeEach(() => {
    authServiceMock.ensureAuthenticated.mockReset();
    authServiceMock.hasModule.mockReset();
    authServiceMock.isAdminActor.mockReset();
    routerMock.createUrlTree.mockReset();
  });

  async function runWithProviders<T>(guardCall: () => Promise<T>): Promise<T> {
    const providers: Provider[] = [
      { provide: AuthService, useValue: authServiceMock },
      { provide: Router, useValue: routerMock },
    ];
    const injector = createEnvironmentInjector(providers, null);

    try {
      return await runInInjectionContext(injector, guardCall);
    } finally {
      injector.destroy();
    }
  }

  it('redirects unauthenticated user to login and preserves redirect target', async () => {
    authServiceMock.ensureAuthenticated.mockResolvedValue(false);

    const result = await runWithProviders(() =>
      authGuard({} as never, { url: '/dossiers' } as RouterStateSnapshot),
    );

    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/login'], {
      queryParams: { redirectTo: '/dossiers' },
    });
    expect(result).toEqual({
      commands: ['/login'],
      extras: { queryParams: { redirectTo: '/dossiers' } },
    });
  });

  it('redirects authenticated anonymous route access to dashboard', async () => {
    authServiceMock.ensureAuthenticated.mockResolvedValue(true);

    const result = await runWithProviders(() => anonymousGuard({} as never, {} as never));
    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/dashboard']);
    expect(result).toEqual({
      commands: ['/dashboard'],
      extras: undefined,
    });
  });

  it('blocks module route when entitlement is missing', async () => {
    authServiceMock.ensureAuthenticated.mockResolvedValue(true);
    authServiceMock.hasModule.mockReturnValue(false);

    const result = await runWithProviders(() =>
      moduleGuard({ data: { requiredModule: 'watchlist' } } as never, {} as never),
    );

    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/dashboard']);
    expect(result).toEqual({
      commands: ['/dashboard'],
      extras: undefined,
    });
  });

  it('allows admin route for admin actor', async () => {
    authServiceMock.ensureAuthenticated.mockResolvedValue(true);
    authServiceMock.isAdminActor.mockReturnValue(true);

    const result = await runWithProviders(() => adminGuard({} as never, {} as never));

    expect(result).toBe(true);
  });

  it('redirects non-admin actor away from admin route', async () => {
    authServiceMock.ensureAuthenticated.mockResolvedValue(true);
    authServiceMock.isAdminActor.mockReturnValue(false);

    const result = await runWithProviders(() => adminGuard({} as never, {} as never));

    expect(routerMock.createUrlTree).toHaveBeenCalledWith(['/dashboard']);
    expect(result).toEqual({
      commands: ['/dashboard'],
      extras: undefined,
    });
  });
});
