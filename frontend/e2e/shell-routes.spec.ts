import { expect, test } from '@playwright/test';

test.describe('frontend auth routes', () => {
  test('redirects unauthenticated root route to login', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL(/\/login\?redirectTo=%2Fdashboard$/);
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
  });

  test('redirects protected route to login with redirect query', async ({ page }) => {
    await page.goto('/dossiers');

    await expect(page).toHaveURL(/\/login\?redirectTo=%2Fdossiers$/);
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
  });

  test('redirects search route to login with redirect query', async ({ page }) => {
    await page.goto('/searches');

    await expect(page).toHaveURL(/\/login\?redirectTo=%2Fsearches$/);
    await expect(page.getByRole('heading', { name: 'Вход' })).toBeVisible();
  });

  test('shows shell route for authenticated session with backend auth-context mock', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'analyst@acme.decider.local',
          tenant_id: 'acme',
          roles: ['user'],
          scopes: ['read:data', 'watchlist:view'],
          module_entitlements: ['dashboard', 'watchlist'],
        }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/watchlist');

    await expect(page).toHaveURL(/\/watchlist$/);
    await expect(page.getByRole('heading', { name: 'Decider' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Watchlist' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Dossiers' })).toHaveCount(0);
  });

  test('shows not found route for authenticated unknown path', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'analyst@acme.decider.local',
          tenant_id: 'acme',
          roles: ['user'],
          scopes: ['read:data'],
          module_entitlements: ['dashboard'],
        }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/route-that-does-not-exist');

    await expect(page.getByRole('heading', { name: 'Not Found' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to dashboard' })).toBeVisible();
  });

  test('renders search workflow and shell navigation for dossiers-enabled user', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'analyst@acme.decider.local',
          tenant_id: 'acme',
          roles: ['user'],
          scopes: ['read:data'],
          module_entitlements: ['dashboard', 'dossiers'],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/dossiers', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          dossiers: [
            {
              tenant_id: 'acme',
              dossier_id: 'dos-1',
              subject_name: 'Acme LLP',
              subject_type: 'organization',
              created_at: '2026-03-02T10:00:00Z',
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/search-requests', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          search_requests: [
            {
              tenant_id: 'acme',
              request_id: 'req-1',
              dossier_id: 'dos-1',
              query_text: 'open sanctions check',
              status: 'queued',
              created_at: '2026-03-02T11:00:00Z',
            },
          ],
        }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/searches');

    await expect(page.getByRole('heading', { name: 'Search request workflow' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Dossiers' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Searches' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Exports' })).toBeVisible();
    await expect(page.getByText('open sanctions check')).toBeVisible();
  });

  test('renders admin workspace for admin actor and persists entitlement update', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'admin-1',
          tenant_id: 'acme',
          roles: ['admin'],
          scopes: ['read:data', 'entitlements:write'],
          module_entitlements: ['dashboard'],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/audit/events', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          events: [
            {
              event_id: 'evt-1',
              action: 'entitlements.updated',
              actor_subject: 'admin-1',
              target_subject: 'user-123',
              tenant_id: 'acme',
              outcome: 'success',
              occurred_at: '2026-03-02T12:00:00Z',
              reason: null,
            },
          ],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/entitlements/user-123', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            tenant_id: 'acme',
            subject: 'user-123',
            enabled_modules: ['dashboard'],
            audit_metadata: null,
          }),
        });
        return;
      }

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          subject: 'user-123',
          enabled_modules: ['dashboard', 'watchlist'],
          audit_metadata: {
            event_id: 'evt-2',
            action: 'entitlements.updated',
            actor_subject: 'admin-1',
            target_subject: 'user-123',
            tenant_id: 'acme',
            occurred_at: '2026-03-02T12:05:00Z',
          },
        }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/admin');

    await expect(page.getByRole('heading', { name: 'Entitlements and audit control' })).toBeVisible();
    await expect(page.getByRole('navigation', { name: 'Primary' }).getByRole('link', { name: 'Admin' })).toBeVisible();

    await page.getByLabel('Subject').fill('user-123');
    await page.getByRole('button', { name: 'Load entitlements' }).click();
    await page.getByRole('checkbox', { name: /Watchlist/i }).check();
    await page.getByRole('button', { name: 'Save entitlements' }).click();

    await expect(
      page.getByText(
        'Entitlements updated for user-123. The subject will see changes after the next auth-context refresh.',
      ),
    ).toBeVisible();
    await expect(page.locator('.audit-card strong').filter({ hasText: 'Entitlements updated' })).toBeVisible();
  });

  test('redirects non-admin user away from admin route', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'analyst@acme.decider.local',
          tenant_id: 'acme',
          roles: ['user'],
          scopes: ['read:data'],
          module_entitlements: ['dashboard', 'dossiers'],
        }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/admin');

    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0);
  });

  test('shows explicit backend-forbidden feedback for export request', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'analyst@acme.decider.local',
          tenant_id: 'acme',
          roles: ['user'],
          scopes: ['read:data'],
          module_entitlements: ['dashboard', 'dossiers'],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/dossiers', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          dossiers: [],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/search-requests', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          tenant_id: 'acme',
          search_requests: [],
        }),
      });
    });

    await page.route('**/api/v1/tenants/acme/exports', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Forbidden' }),
      });
    });

    await page.addInitScript(() => {
      window.sessionStorage.setItem(
        'decider.auth.session.v1',
        JSON.stringify({
          accessToken: 'fake-access-token',
          tokenType: 'Bearer',
          idToken: null,
          refreshToken: null,
          expiresAt: Date.now() + 10 * 60 * 1000,
        }),
      );
    });

    await page.goto('/exports');
    await page.getByRole('button', { name: 'Request export' }).click();

    await expect(
      page.getByText(
        'Export request was rejected by the backend. The current session does not satisfy tenant or scope requirements.',
      ),
    ).toBeVisible();
  });
});
