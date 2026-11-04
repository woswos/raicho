import type { ApiDocument, ApiError } from './api_generated.js';
import validateApi from './api_validator_generated.js';

export type Failure = { kind: 'api'; code: ApiError } | { kind: 'network' } | { kind: 'timeout' } | { kind: 'invalid' };

export type Outcome<Document> = { ok: true; document: Document } | { ok: false; failure: Failure };

// The server answers a mail request within its 15-second connector deadline.
export const REQUEST_TIMEOUT_MS = 20000;

/** A route under `prefix` that names one opaque handle, encoded as a single path segment. */
export function apiPath(prefix: string, handle: string, suffix = ''): string {
  return `${prefix}/${encodeURIComponent(handle)}${suffix}`;
}

interface Options {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
}

/** Sends one same-origin JSON request and validates the document it returns. */
export async function apiRequest<Document extends ApiDocument>(
  path: string,
  options: Options = {},
): Promise<Outcome<Document | null>> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort('timeout'), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(path, {
      method: options.method ?? 'GET',
      credentials: 'same-origin',
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
        ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
      },
      ...(options.body === undefined ? {} : { body: JSON.stringify(options.body) }),
      signal: controller.signal,
    });
    if (response.status === 204) return { ok: true, document: null };
    let document: unknown;
    try {
      document = await response.json();
    } catch {
      return { ok: false, failure: { kind: 'invalid' } };
    }
    if (!validateApi(document)) return { ok: false, failure: { kind: 'invalid' } };
    if ('error' in document) return { ok: false, failure: { kind: 'api', code: document.error } };
    if (!response.ok) return { ok: false, failure: { kind: 'invalid' } };
    return { ok: true, document: document as Document };
  } catch {
    return { ok: false, failure: { kind: controller.signal.reason === 'timeout' ? 'timeout' : 'network' } };
  } finally {
    window.clearTimeout(timer);
  }
}
