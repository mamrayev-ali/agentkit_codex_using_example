export const environment = {
  production: true,
  name: 'production',
  apiBaseUrl: '/api/v1',
  oidc: {
    issuerUrl: '/realms/decider-local',
    clientId: 'decider-frontend',
    redirectPath: '/auth/callback',
    postLogoutRedirectPath: '/login',
    scopes: 'openid profile email',
  },
} as const;
