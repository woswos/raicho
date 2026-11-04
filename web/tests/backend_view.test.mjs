import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { describeBackend } = await import(pathToFileURL(resolve(outputDirectory, 'backend_view.js')).href);

const backend = (status, lastError = null) => ({ status, kind: 'thunderbird', last_error: lastError });

test('each connector state has a label and a severity', () => {
  for (const [status, label, state] of [
    ['connected', 'Connected', 'ready'],
    ['disconnected', 'Disconnected', 'waiting'],
    ['unconfigured', 'Not configured', 'waiting'],
    ['revoked', 'Access revoked', 'error'],
    ['unavailable', 'Unavailable', 'error'],
  ]) {
    const description = describeBackend(backend(status));
    assert.equal(description.label, label, status);
    assert.equal(description.state, state, status);
    assert.ok(description.description.length > 10, status);
  }
  assert.equal(describeBackend(backend('connected')).description, 'Thunderbird is connected.');
  assert.match(describeBackend(backend('unavailable')).description, /application database/u);
});

test('a disconnection explains its last error, and other states ignore it', () => {
  const waiting = describeBackend(backend('disconnected')).description;
  const timedOut = describeBackend(backend('disconnected', 'heartbeat_timeout')).description;
  assert.notEqual(timedOut, waiting);
  assert.match(timedOut, /stopped responding/u);
  assert.equal(
    describeBackend(backend('disconnected', 'invalid_message')).description,
    describeBackend(backend('disconnected', 'stale_generation')).description,
  );
  assert.match(describeBackend(backend('disconnected', 'incompatible_version')).description, /incompatible/u);
  assert.equal(describeBackend(backend('connected', 'heartbeat_timeout')).description, 'Thunderbird is connected.');
});
