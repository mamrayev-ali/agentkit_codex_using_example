import { expect, test } from '@playwright/test';

test.describe('frontend auth routes', () => {
  test('redirects unauthenticated root route to login', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL(/\/login\?redirectTo=%2Fdashboard$/);
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  });

  test('redirects protected route to login with redirect query', async ({ page }) => {
    await page.goto('/dossiers');

    await expect(page).toHaveURL(/\/login\?redirectTo=%2Fdossiers$/);
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  });

  test('shows shell route for authenticated session with backend auth-context mock', async ({ page }) => {
    await page.route('**/api/v1/auth/context', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          authenticated: true,
          subject: 'demo-user',
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
          subject: 'demo-user',
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
});
