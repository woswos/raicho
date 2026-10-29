import type { Authenticate } from './contract_generated.js';

// Every derived key depends on these exact bytes, so the label keeps its original "client" wording.
const CONNECTOR_KEY_LABEL = 'raicho connector client key';
const SERVER_KEY_LABEL = 'raicho connector server key';
const encoder = new TextEncoder();

export type AuthenticationFields = Omit<Authenticate, 'type' | 'client_proof'>;

export function toHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export type Bytes = Uint8Array<ArrayBuffer>;

export async function hmac(key: Bytes, message: string): Promise<Bytes> {
  const imported = await crypto.subtle.importKey('raw', key, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return new Uint8Array(await crypto.subtle.sign('HMAC', imported, encoder.encode(message)));
}

export function randomNonce(): string {
  return toHex(crypto.getRandomValues(new Uint8Array(32)));
}

export function authenticationMessage(serverNonce: string, fields: AuthenticationFields): string {
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

export async function clientProof(token: string, message: string): Promise<string> {
  const connectorKey = await hmac(encoder.encode(token), CONNECTOR_KEY_LABEL);
  const storedKey = new Uint8Array(await crypto.subtle.digest('SHA-256', connectorKey));
  const signature = await hmac(storedKey, message);
  return toHex(connectorKey.map((byte, index) => byte ^ (signature[index] ?? 0)));
}

export function serverKey(token: string): Promise<Bytes> {
  return hmac(encoder.encode(token), SERVER_KEY_LABEL);
}

export async function serverSignature(token: string, message: string): Promise<string> {
  return toHex(await hmac(await serverKey(token), message));
}

// Comparing secrets byte by byte in constant time keeps their timing from leaking matches.
export function constantTimeEqual(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

export async function verifyServerSignature(token: string, message: string, signature: string): Promise<boolean> {
  return constantTimeEqual(await serverSignature(token, message), signature);
}
