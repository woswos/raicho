import type { Authenticate } from './contract_generated.js';

const CLIENT_KEY_LABEL = 'raicho connector client key';
const SERVER_KEY_LABEL = 'raicho connector server key';
const encoder = new TextEncoder();

export type AuthenticationFields = Omit<Authenticate, 'type' | 'client_proof'>;

function hex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join(
    '',
  );
}

type Bytes = Uint8Array<ArrayBuffer>;

async function hmac(key: Bytes, message: string): Promise<Bytes> {
  const imported = await crypto.subtle.importKey(
    'raw',
    key,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  );
  return new Uint8Array(
    await crypto.subtle.sign('HMAC', imported, encoder.encode(message)),
  );
}

export function randomNonce(): string {
  return hex(crypto.getRandomValues(new Uint8Array(32)));
}

export function authenticationMessage(
  serverNonce: string,
  fields: AuthenticationFields,
): string {
  return [
    'raicho-connector-authentication',
    String(fields.protocol_version),
    serverNonce,
    fields.client_nonce,
    fields.backend_kind,
    fields.backend_version,
    fields.connector_version,
    String(fields.capabilities.length),
    ...fields.capabilities,
  ].join('\n');
}

export async function clientProof(
  token: string,
  message: string,
): Promise<string> {
  const clientKey = await hmac(encoder.encode(token), CLIENT_KEY_LABEL);
  const storedKey = new Uint8Array(
    await crypto.subtle.digest('SHA-256', clientKey),
  );
  const signature = await hmac(storedKey, message);
  return hex(clientKey.map((byte, index) => byte ^ (signature[index] ?? 0)));
}

export async function serverSignature(
  token: string,
  message: string,
): Promise<string> {
  const serverKey = await hmac(encoder.encode(token), SERVER_KEY_LABEL);
  return hex(await hmac(serverKey, message));
}
