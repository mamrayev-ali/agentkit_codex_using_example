import { defineConfig, devices } from '@playwright/test';

const _USE_RUNTIME_STACK = process.env.DECIDER_E2E_RUNTIME === '1';
const _DEFAULT_BASE_URL = 'http://127.0.0.1:4200';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: !_USE_RUNTIME_STACK,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.DECIDER_E2E_UI_BASE_URL ?? _DEFAULT_BASE_URL,
    trace: 'on-first-retry',
  },
  webServer: _USE_RUNTIME_STACK
    ? undefined
    : {
        command: 'pnpm start',
        url: 'http://127.0.0.1:4200',
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
