import type { APIRequestContext, Browser, BrowserContext, Page } from '@playwright/test';

const _SESSION_KEY = 'decider.auth.session.v1';
const _DEFAULT_UI_BASE_URL = 'http://localhost:4200';
const _DEFAULT_API_BASE_URL =
  process.env.IN_DEV_CONTAINER === '1'
    ? 'http://api:8000/api/v1'
    : 'http://127.0.0.1:8000/api/v1';
const _PROXIED_UI_BASE_URL =
  process.env.IN_DEV_CONTAINER === '1' ? 'http://frontend:4200' : _DEFAULT_UI_BASE_URL;
const _BROWSER_VISIBLE_UI_ORIGINS = ['http://localhost:4200', 'http://127.0.0.1:4200'];
const _BROWSER_VISIBLE_API_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000'];
const _DEFAULT_ISSUER_URL =
  process.env.IN_DEV_CONTAINER === '1'
    ? 'http://keycloak:8080/realms/decider-local'
    : 'http://127.0.0.1:8080/realms/decider-local';
const _TOKEN_ENDPOINT = `${process.env.DECIDER_E2E_KEYCLOAK_ISSUER ?? _DEFAULT_ISSUER_URL}/protocol/openid-connect/token`;
const _TOKEN_CLIENT_ID = process.env.DECIDER_E2E_CLI_CLIENT_ID ?? 'decider-cli';

export type RuntimeActor = 'demo-user' | 'demo-admin';

export type RuntimePage = {
  context: BrowserContext;
  page: Page;
};

function readActorPassword(actor: RuntimeActor): string {
  const password =
    actor === 'demo-user'
      ? process.env.DECIDER_KEYCLOAK_DEMO_USER_PASSWORD
      : process.env.DECIDER_KEYCLOAK_DEMO_ADMIN_PASSWORD;

  if (typeof password !== 'string' || !password.trim()) {
    throw new Error(`Runtime walkthrough password for ${actor} is missing.`);
  }

  return password.trim();
}

export function runtimeWalkthroughEnabled(): boolean {
  return (
    process.env.DECIDER_E2E_RUNTIME === '1' &&
    typeof process.env.DECIDER_KEYCLOAK_DEMO_USER_PASSWORD === 'string' &&
    !!process.env.DECIDER_KEYCLOAK_DEMO_USER_PASSWORD.trim() &&
    typeof process.env.DECIDER_KEYCLOAK_DEMO_ADMIN_PASSWORD === 'string' &&
    !!process.env.DECIDER_KEYCLOAK_DEMO_ADMIN_PASSWORD.trim()
  );
}

async function fetchActorAccessToken(
  request: APIRequestContext,
  actor: RuntimeActor,
): Promise<string> {
  const response = await request.post(_TOKEN_ENDPOINT, {
    form: {
      grant_type: 'password',
      client_id: _TOKEN_CLIENT_ID,
      username: actor,
      password: readActorPassword(actor),
    },
  });

  if (!response.ok()) {
    throw new Error(
      `Unable to fetch a runtime access token for ${actor}. ` +
        `Token endpoint responded with ${response.status()}.`,
    );
  }

  const payload = (await response.json()) as Record<string, unknown>;
  const accessToken = payload['access_token'];
  if (typeof accessToken !== 'string' || !accessToken.trim()) {
    throw new Error(`Runtime token payload for ${actor} is missing access_token.`);
  }

  return accessToken;
}

function buildRuntimeSession(accessToken: string): Record<string, unknown> {
  return {
    accessToken,
    tokenType: 'Bearer',
    idToken: null,
    refreshToken: null,
    expiresAt: Date.now() + 10 * 60 * 1000,
  };
}

async function seedRuntimeSession(page: Page, accessToken: string): Promise<void> {
  await page.evaluate(
    ({ sessionKey, sessionValue }) => {
      window.sessionStorage.setItem(sessionKey, JSON.stringify(sessionValue));
    },
    {
      sessionKey: _SESSION_KEY,
      sessionValue: buildRuntimeSession(accessToken),
    },
  );
}

async function wireContainerProxyRoutes(context: BrowserContext): Promise<void> {
  for (const origin of _BROWSER_VISIBLE_UI_ORIGINS) {
    await context.route(`${origin}/**`, async (route) => {
      const forwardedUrl = route.request().url().replace(origin, _PROXIED_UI_BASE_URL);
      const response = await route.fetch({ url: forwardedUrl });
      await route.fulfill({ response });
    });
  }

  const proxiedApiOrigin = _DEFAULT_API_BASE_URL.replace(/\/api\/v1$/, '');
  for (const origin of _BROWSER_VISIBLE_API_ORIGINS) {
    await context.route(`${origin}/**`, async (route) => {
      const forwardedUrl = route.request().url().replace(origin, proxiedApiOrigin);
      const response = await route.fetch({ url: forwardedUrl });
      await route.fulfill({ response });
    });
  }
}

export async function createAuthenticatedPage(
  browser: Browser,
  request: APIRequestContext,
  actor: RuntimeActor,
): Promise<RuntimePage> {
  const accessToken = await fetchActorAccessToken(request, actor);
  const context = await browser.newContext({
    baseURL: process.env.DECIDER_E2E_UI_BASE_URL ?? _DEFAULT_UI_BASE_URL,
  });

  if (process.env.IN_DEV_CONTAINER === '1') {
    await wireContainerProxyRoutes(context);
  }

  await context.addInitScript(
    ({ sessionKey, sessionValue }) => {
      window.sessionStorage.setItem(sessionKey, JSON.stringify(sessionValue));
    },
    {
      sessionKey: _SESSION_KEY,
      sessionValue: buildRuntimeSession(accessToken),
    },
  );

  const page = await context.newPage();
  await page.goto('/login', { waitUntil: 'domcontentloaded' });
  await seedRuntimeSession(page, accessToken);
  return { context, page };
}

export async function fetchRuntimeAuthContext(
  request: APIRequestContext,
  actor: RuntimeActor,
): Promise<Record<string, unknown>> {
  const accessToken = await fetchActorAccessToken(request, actor);
  const response = await request.get(
    `${process.env.DECIDER_E2E_API_BASE_URL ?? _DEFAULT_API_BASE_URL}/auth/context`,
    {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  );

  if (!response.ok()) {
    throw new Error(
      `Unable to fetch runtime auth-context for ${actor}. ` +
        `API responded with ${response.status()}.`,
    );
  }

  return (await response.json()) as Record<string, unknown>;
}
