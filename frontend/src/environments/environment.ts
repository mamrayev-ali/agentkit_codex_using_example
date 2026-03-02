export const environment = {
  production: false,
  name: 'development',
  apiBaseUrl: 'http://localhost:8000/api/v1',
  oidc: {
    issuerUrl: 'http://localhost:8080/realms/decider-local',
    clientId: 'decider-frontend',
    redirectPath: '/auth/callback',
    postLogoutRedirectPath: '/login',
    // The checked-in local Keycloak realm exposes only `openid` plus app scopes.
    scopes: 'openid',
  },
} as const;
