const _UNRESERVED = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';

function toBase64Url(input: ArrayBuffer): string {
  const bytes = new Uint8Array(input);
  let binary = '';
  for (const value of bytes) {
    binary += String.fromCharCode(value);
  }

  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function randomUnreserved(length: number): string {
  const buffer = new Uint8Array(length);
  crypto.getRandomValues(buffer);

  const chars: string[] = [];
  for (const value of buffer) {
    chars.push(_UNRESERVED[value % _UNRESERVED.length]);
  }

  return chars.join('');
}

export async function createPkceMaterial(): Promise<{
  state: string;
  codeVerifier: string;
  codeChallenge: string;
}> {
  const state = randomUnreserved(48);
  const codeVerifier = randomUnreserved(64);

  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(codeVerifier));
  const codeChallenge = toBase64Url(digest);

  return {
    state,
    codeVerifier,
    codeChallenge,
  };
}
