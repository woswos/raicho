import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const { parseConfiguration } = await import(
  pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'extension/src/configuration.js')).href
);
const token = 'a'.repeat(64);
const invalid = { message: 'Managed connector configuration is invalid.' };

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
  assert.equal(parseConfiguration({ endpoint: 'wss://probe/lifecycle', token }).endpoint, 'wss://probe/lifecycle');
});

test('rejects malformed managed configuration without exposing values', () => {
  const malformed = [
    null,
    [],
    'private value',
    { endpoint: 'ws://probe/lifecycle' },
    { token },
    { endpoint: 'ws://probe/lifecycle', token: 123 },
  ];
  for (const configuration of malformed) {
    assert.throws(() => parseConfiguration(configuration), invalid);
  }
});

test('agrees with the shared connector configuration rules', async () => {
  const rules = JSON.parse(
    await readFile(new URL('../../protocol/fixtures/configuration/connector.json', import.meta.url), 'utf8'),
  );
  const endpoint = rules.endpoints.valid[0];
  for (const valid of rules.tokens.valid) {
    assert.equal(parseConfiguration({ endpoint, token: valid }).token, valid);
  }
  for (const rejected of rules.tokens.invalid) {
    assert.throws(() => parseConfiguration({ endpoint, token: rejected }), invalid);
  }
  for (const valid of rules.endpoints.valid) {
    assert.equal(parseConfiguration({ endpoint: valid, token }).endpoint, valid);
  }
  for (const rejected of rules.endpoints.invalid) {
    assert.throws(() => parseConfiguration({ endpoint: rejected, token }), invalid, JSON.stringify(rejected));
  }
});
