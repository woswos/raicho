import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { parseStatus, StatusResponseError } = await import(
  pathToFileURL(resolve(outputDirectory, 'status.js')).href
);

function response(backend) {
  return {
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: {
      kind: 'thunderbird',
      generation: null,
      last_error: null,
      heartbeat_count: 0,
      ...backend,
    },
    version: '0.1.0',
    commit: 'unknown',
  };
}

test('accepts connector states without coupling application readiness', () => {
  for (const status of [
    'unconfigured',
    'connected',
    'disconnected',
    'revoked',
    'unavailable',
  ]) {
    assert.equal(parseStatus(response({ status })).backend.status, status);
  }
});

test('retains fixed diagnostic codes but discards connection internals', () => {
  const parsed = parseStatus(
    response({
      status: 'disconnected',
      last_error: 'heartbeat_timeout',
      generation: 'a'.repeat(32),
      heartbeat_count: 7,
    }),
  );
  assert.deepEqual(parsed.backend, {
    kind: 'thunderbird',
    status: 'disconnected',
    last_error: 'heartbeat_timeout',
  });
});

test('rejects unknown states and arbitrary backend error text safely', () => {
  for (const backend of [
    { status: 'unknown' },
    { status: 'connected', last_error: 'private backend text' },
    { status: 'disconnected', last_error: 42 },
    { status: 'revoked', last_error: '<script>private</script>' },
  ]) {
    assert.throws(() => parseStatus(response(backend)), StatusResponseError);
  }
});
