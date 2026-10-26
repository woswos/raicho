import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';

const { startManagedConnector } = await import(
  pathToFileURL(
    resolve(
      process.env.RAICHO_EXTENSION_BUILD_DIR,
      'extension/src/managed_connector.js',
    ),
  ).href
);
const token = 'a'.repeat(64);
const endpoint = 'ws://connector-proxy:8081/connector/v1';
function fixture() {
  let resolveSettings;
  const connections = [];
  const api = {
    storage: {
      managed: {
        get: () =>
          new Promise((resolve) => {
            resolveSettings = resolve;
          }),
      },
    },
    runtime: {
      getBrowserInfo: async () => ({ version: '153.5.0' }),
      getManifest: () => ({ version: '0.2.0' }),
    },
  };
  const stop = startManagedConnector(api, (configuration, metadata) => {
    const connection = { configuration, metadata, stopped: false };
    connections.push(connection);
    return () => {
      connection.stopped = true;
    };
  });
  return {
    connections,
    stop,
    async settle(value) {
      resolveSettings(value);
      await setImmediate();
    },
  };
}

test('starts from managed settings without unsupported managed change events', async () => {
  const state = fixture();
  assert.equal(state.connections.length, 0);
  await state.settle({ endpoint, token });
  assert.deepEqual(state.connections[0], {
    configuration: { endpoint, token },
    metadata: { backendVersion: '153.5.0', connectorVersion: '0.2.0' },
    stopped: false,
  });
  state.stop();
  assert.equal(state.connections[0].stopped, true);
});

test('remains inactive without provisioned settings', async () => {
  const state = fixture();
  await state.settle({});
  assert.equal(state.connections.length, 0);
  state.stop();
});

test('ignores asynchronous settings after shutdown', async () => {
  const state = fixture();
  state.stop();
  await state.settle({ endpoint, token });
  assert.equal(state.connections.length, 0);
});

test('invalid configuration cannot start the transport', async () => {
  const state = fixture();
  await state.settle({ endpoint, token: 'private' });
  assert.equal(state.connections.length, 0);
  state.stop();
});
