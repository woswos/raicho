import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import { probeFixture } from './probe_fixture.mjs';

const { startLifecycleProbe } = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'lifecycle_probe.js'),
  ).href
);
const configuration = {
  endpoint: 'ws://probe:8765/lifecycle',
  token: 'a'.repeat(64),
};
const metadata = {
  extension_version: '0.1.0',
  browser_version: '153.5.0',
  session_id: 'test-session',
};

test('sends the token only on open and retains its session while idle', () => {
  const fixture = probeFixture();
  const stop = startLifecycleProbe(
    configuration,
    metadata,
    fixture.dependencies,
  );
  const socket = fixture.sockets[0];
  socket.open();
  assert.deepEqual(socket.sent, [
    {
      ...metadata,
      type: 'lifecycle_probe',
      token: configuration.token,
      sequence: 0,
    },
  ]);
  fixture.fireTimer(10000);
  fixture.fireTimer(10000);
  assert.deepEqual(socket.sent.slice(1), [
    { ...metadata, type: 'lifecycle_heartbeat', sequence: 1 },
    { ...metadata, type: 'lifecycle_heartbeat', sequence: 2 },
  ]);
  stop();
  assert.equal(fixture.timers.size, 0);
  assert.equal(socket.readyState, 3);
});

test('bounds failed connection attempts and ignores stale socket events', () => {
  const fixture = probeFixture();
  const stop = startLifecycleProbe(
    configuration,
    metadata,
    fixture.dependencies,
  );
  const stale = fixture.sockets[0];
  for (const delay of [1000, 2000, 4000, 8000, 16000, 30000, 30000]) {
    fixture.fireTimer(5000);
    assert.equal(fixture.timers.size, 1);
    stale.open();
    assert.equal(stale.sent.length, 0);
    fixture.fireTimer(delay);
  }
  stop();
});

test('keeps its session across reconnect and stops on rejection', () => {
  const fixture = probeFixture();
  startLifecycleProbe(configuration, metadata, fixture.dependencies);
  const first = fixture.sockets[0];
  first.open();
  fixture.fireTimer(10000);
  first.close();
  fixture.fireTimer(1000);
  const second = fixture.sockets[1];
  second.open();
  assert.equal(second.sent[0].sequence, 0);
  assert.equal(second.sent[0].session_id, metadata.session_id);
  second.onclose({ code: 4003 });
  assert.equal(fixture.timers.size, 0);
});

test('closes a blocked sender and recovers from socket construction failure', () => {
  const fixture = probeFixture();
  const stop = startLifecycleProbe(
    configuration,
    metadata,
    fixture.dependencies,
  );
  fixture.sockets[0].open();
  fixture.sockets[0].bufferedAmount = 4097;
  fixture.fireTimer(10000);
  assert.equal(fixture.sockets[0].readyState, 3);
  fixture.dependencies.connect = () => {
    throw new Error('Private endpoint');
  };
  fixture.fireTimer(1000);
  assert.equal(fixture.timers.size, 1);
  stop();
  assert.equal(fixture.timers.size, 0);
});
