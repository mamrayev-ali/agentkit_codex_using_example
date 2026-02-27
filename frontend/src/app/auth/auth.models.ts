export interface OidcConfig {
  issuerUrl: string;
  clientId: string;
  redirectPath: string;
  postLogoutRedirectPath: string;
  scopes: string;
}

export interface AuthSession {
  accessToken: string;
  tokenType: string;
  idToken: string | null;
  refreshToken: string | null;
  expiresAt: number;
}

export interface PendingLoginRequest {
  state: string;
  codeVerifier: string;
  redirectTo: string;
  createdAt: number;
}

export interface AuthContext {
  authenticated: true;
  subject: string;
  tenantId: string;
  roles: string[];
  scopes: string[];
  moduleEntitlements: string[];
}

export interface OidcTokenPayload {
  access_token: string;
  token_type?: string;
  expires_in?: number;
  id_token?: string;
  refresh_token?: string;
}

export type AuthCallbackResult =
  | {
      ok: true;
      redirectTo: string;
    }
  | {
      ok: false;
      message: string;
    };
