import { expect, test } from '@playwright/test';

test.describe('frontend shell routes', () => {
  test('loads dashboard on root route', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Decider' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('navigates to dossiers route from shell navigation', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Dossiers' }).click();

    await expect(page).toHaveURL(/\/dossiers$/);
    await expect(page.getByRole('heading', { name: 'Dossiers' })).toBeVisible();
  });

  test('shows not found page for unknown route', async ({ page }) => {
    await page.goto('/route-that-does-not-exist');

    await expect(page.getByRole('heading', { name: 'Not Found' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Back to dashboard' })).toBeVisible();
  });
});
