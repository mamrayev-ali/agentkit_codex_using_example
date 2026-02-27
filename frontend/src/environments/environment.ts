export const environment = {
  production: false,
  name: 'development',
  apiBaseUrl: 'http://localhost:8000/api/v1',
  oidc: {
    issuerUrl: 'http://localhost:8080/realms/decider-local',
    clientId: 'decider-frontend',
    redirectPath: '/auth/callback',
    postLogoutRedirectPath: '/login',
    scopes: 'openid profile email',
  },
} as const;
