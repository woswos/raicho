import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { parseStatus, StatusResponseError } = await import(
  pathToFileURL(resolve(outputDirectory, 'status.js')).href
);

function readyStatus() {
  return {
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: { status: 'unconfigured', kind: 'thunderbird', last_error: null },
    version: '0.1.0',
    commit: 'unknown',
  };
}

test('accepts the server contract without claiming a connected backend', () => {
  const response = readyStatus();
  const parsed = parseStatus(response);
  assert.deepEqual(parsed, response);
  assert.notEqual(parsed, response);
  assert.notEqual(parsed.database, response.database);
});

test('ignores additional response data instead of retaining it', () => {
  assert.deepEqual(
    parseStatus({
      ...readyStatus(),
      extra: { content: 'not diagnostic data' },
    }),
    readyStatus(),
  );
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
    { ...readyStatus(), backend: { status: 'unconfigured', kind: 'other' } },
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
    assert.throws(() => parseStatus(response), StatusResponseError);
  }
});

test('rejects malformed database versions with a safe diagnostic', () => {
  for (const version of [undefined, null, 3.51, '', ' ', 'x'.repeat(81)]) {
    assert.throws(
      () =>
        parseStatus({
          ...readyStatus(),
          database: { status: 'ready', engine: 'sqlite', version },
        }),
      { message: 'Raicho returned an unexpected status response.' },
    );
  }
});
