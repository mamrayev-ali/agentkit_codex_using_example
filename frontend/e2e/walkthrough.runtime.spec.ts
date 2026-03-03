import { expect, test, type Page } from '@playwright/test';

import {
  createAuthenticatedPage,
  fetchRuntimeAuthContext,
  runtimeWalkthroughEnabled,
} from './runtime-auth';

async function expectHeading(page: Page, name: string): Promise<void> {
  try {
    await expect(page.getByRole('heading', { name })).toBeVisible({ timeout: 15_000 });
  } catch (error) {
    const bodyText = await page
      .locator('body')
      .innerText()
      .then((value) => value.slice(0, 400))
      .catch(() => '<body unavailable>');
    throw new Error(
      `Expected heading "${name}" on ${page.url()} but it was not visible. Body snippet: ${bodyText}`,
      { cause: error },
    );
  }
}

async function expectTextVisible(page: Page, text: string | RegExp): Promise<void> {
  const locator =
    typeof text === 'string'
      ? page.getByText(text, { exact: true }).first()
      : page.getByText(text).first();
  await expect(locator).toBeVisible({ timeout: 15_000 });
}

test.describe('runtime walkthrough journeys', () => {
  test.describe.configure({ mode: 'serial' });
  test.skip(
    !runtimeWalkthroughEnabled(),
    'Runtime walkthrough suite requires DECIDER_E2E_RUNTIME=1 and seeded demo credentials.',
  );

  test('covers the seeded user and admin walkthrough against the runtime stack', async ({
    browser,
    request,
  }) => {
    const user = await createAuthenticatedPage(browser, request, 'demo-user');
    try {
      await user.page.goto('/dashboard');
      await user.page.waitForLoadState('networkidle');

      await expectHeading(user.page, 'Tenant workflow overview');
      await expectTextVisible(user.page, 'Acme Logistics LLP');
      await expectTextVisible(user.page, 'Aida Sarsen');
      await expect(user.page.getByText('Umbrella Industrial JSC')).toHaveCount(0);

      await user.page.goto('/dossiers');
      await user.page.waitForLoadState('networkidle');
      await expectHeading(user.page, 'Tenant dossier workspace');
      await expectTextVisible(user.page, 'dos-acme-org-001');
      await expectTextVisible(user.page, 'dos-acme-person-001');
      await expect(user.page.getByText('dos-umbrella-org-001')).toHaveCount(0);

      await user.page.goto('/searches');
      await user.page.waitForLoadState('networkidle');
      await expectHeading(user.page, 'Search request workflow');
      await expectTextVisible(user.page, 'open sanctions check');
      await expectTextVisible(user.page, 'court record review');
      await expect(user.page.getByText('req-umbrella-001')).toHaveCount(0);

      await user.page.goto('/exports');
      await user.page.waitForLoadState('networkidle');
      await expectHeading(user.page, 'Export request workflow');
      await user.page.getByRole('button', { name: 'Request export' }).click();
      await expectTextVisible(user.page, /Export export-/);
    } finally {
      await user.context.close();
    }

    const admin = await createAuthenticatedPage(browser, request, 'demo-admin');
    try {
      await admin.page.goto('/admin');
      await admin.page.waitForLoadState('networkidle');

      await expectHeading(admin.page, 'Entitlements and audit control');
      await admin.page.getByLabel('Subject').fill('demo-user');
      await admin.page.getByRole('button', { name: 'Load entitlements' }).click();

      const watchlistCheckbox = admin.page.getByRole('checkbox', { name: /Watchlist/i });
      await expect(watchlistCheckbox).not.toBeChecked();
      await watchlistCheckbox.check();
      await admin.page.getByRole('button', { name: 'Save entitlements' }).click();

      await expect(
        admin.page.getByText(
          'Entitlements updated for demo-user. The subject will see changes after the next auth-context refresh.',
        ),
      ).toBeVisible({ timeout: 15_000 });
      await expect(
        admin.page.locator('.audit-card strong').filter({ hasText: 'Entitlements updated' }),
      ).toHaveCount(2, { timeout: 15_000 });
      await expect(
        admin.page.locator('.audit-card strong').filter({ hasText: 'Export requested' }),
      ).toHaveCount(2, { timeout: 15_000 });
    } finally {
      await admin.context.close();
    }

    const refreshedAuthContext = await fetchRuntimeAuthContext(request, 'demo-user');
    await expect(
      Array.isArray(refreshedAuthContext['module_entitlements']) &&
        refreshedAuthContext['module_entitlements'].includes('watchlist'),
    ).toBeTruthy();

    const updatedUser = await createAuthenticatedPage(browser, request, 'demo-user');
    try {
      await updatedUser.page.goto('/watchlist');
      await updatedUser.page.waitForLoadState('networkidle');

      await expectHeading(updatedUser.page, 'Watchlist');
      await expect(
        updatedUser.page
          .getByRole('navigation', { name: 'Primary' })
          .getByRole('link', { name: 'Watchlist' }),
      ).toBeVisible({ timeout: 15_000 });
    } finally {
      await updatedUser.context.close();
    }
  });
});
