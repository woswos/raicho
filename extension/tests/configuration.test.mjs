import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const { parseConfiguration } = await import(
  pathToFileURL(
    resolve(
      process.env.RAICHO_EXTENSION_BUILD_DIR,
      'extension/src/configuration.js',
    ),
  ).href
);
const token = 'a'.repeat(64);

test('remains inactive when neither managed setting exists', () => {
  assert.equal(parseConfiguration({}), undefined);
});

test('accepts only the configured endpoint and token', () => {
  assert.deepEqual(
    parseConfiguration({
      endpoint: 'ws://probe:8765/lifecycle',
      token,
      extra: 1,
    }),
    { endpoint: 'ws://probe:8765/lifecycle', token },
  );
  assert.equal(
    parseConfiguration({ endpoint: 'wss://probe/lifecycle', token }).endpoint,
    'wss://probe/lifecycle',
  );
});

test('rejects malformed managed configuration without exposing values', () => {
  const malformed = [
    null,
    [],
    'private value',
    { endpoint: 'ws://probe/lifecycle' },
    { token },
    { endpoint: 'https://probe/lifecycle', token },
    { endpoint: 'ws://user:secret@probe/lifecycle', token },
    { endpoint: 'ws://probe/lifecycle?token=secret', token },
    { endpoint: 'ws://probe/lifecycle#secret', token },
    { endpoint: 'not a URL', token },
    { endpoint: 'ws://probe/lifecycle', token: 'short' },
    { endpoint: 'ws://probe/lifecycle', token: token.toUpperCase() },
    { endpoint: 'ws://probe/lifecycle', token: 123 },
  ];
  for (const configuration of malformed) {
    assert.throws(() => parseConfiguration(configuration), {
      message: 'Managed connector configuration is invalid.',
    });
  }
});
