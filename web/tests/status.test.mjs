import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { readStatus } = await import(pathToFileURL(resolve(outputDirectory, 'status.js')).href);

function readyStatus(backend = {}) {
  return {
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: {
      status: 'unconfigured',
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

test('accepts the server contract without claiming a connected backend', () => {
  const response = readyStatus();
  const parsed = readStatus(response);
  assert.deepEqual(parsed, {
    ...response,
    backend: { status: 'unconfigured', kind: 'thunderbird', last_error: null },
  });
  assert.notEqual(parsed.database, response.database);
});

test('accepts connector states without coupling application readiness', () => {
  for (const status of ['unconfigured', 'connected', 'disconnected', 'revoked', 'unavailable']) {
    assert.equal(readStatus(readyStatus({ status })).backend.status, status);
  }
});

test('retains fixed diagnostic codes but discards connection internals', () => {
  const parsed = readStatus(
    readyStatus({
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

test('rejects response data outside the status contract', () => {
  assert.equal(readStatus({ ...readyStatus(), extra: { content: 'not diagnostic data' } }), undefined);
});

test('rejects unknown states and arbitrary backend error text safely', () => {
  for (const backend of [
    { status: 'unknown' },
    { status: 'connected', last_error: 'private backend text' },
    { status: 'disconnected', last_error: 42 },
    { status: 'revoked', last_error: '<script>private</script>' },
  ]) {
    assert.equal(readStatus(readyStatus(backend)), undefined);
  }
});

test('rejects absent, malformed, and incompatible status fields', () => {
  const invalidResponses = [
    null,
    [],
    'ready',
    {},
    { ...readyStatus(), status: 'starting' },
    { ...readyStatus(), database: null },
    { ...readyStatus(), database: [] },
    { ...readyStatus(), database: { status: 'ready', engine: 'sqlite' } },
    {
      ...readyStatus(),
      database: { status: 'failed', engine: 'sqlite', version: '3.51.3' },
    },
    {
      ...readyStatus(),
      database: { status: 'ready', engine: 'other', version: '3.51.3' },
    },
    { ...readyStatus(), backend: { status: 'connected', kind: 'thunderbird' } },
    readyStatus({ kind: 'other' }),
    { ...readyStatus(), backend: null },
    { ...readyStatus(), version: 1 },
    { ...readyStatus(), version: '' },
    { ...readyStatus(), version: '   ' },
    { ...readyStatus(), version: 'a'.repeat(81) },
    { ...readyStatus(), commit: '' },
    { ...readyStatus(), commit: 1 },
    { ...readyStatus(), commit: 'a'.repeat(81) },
  ];
  const missingCommit = readyStatus();
  delete missingCommit.commit;
  invalidResponses.push(missingCommit);

  for (const response of invalidResponses) {
    assert.equal(readStatus(response), undefined);
  }
});

test('rejects malformed database versions', () => {
  for (const version of [undefined, null, 3.51, '', ' ', 'x'.repeat(81)]) {
    assert.equal(readStatus({ ...readyStatus(), database: { status: 'ready', engine: 'sqlite', version } }), undefined);
  }
});
