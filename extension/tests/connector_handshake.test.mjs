import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  configuration,
  connectorFixture,
  generation,
  ping,
  welcome,
} from './connector_fixture.mjs';

test('authenticates once, accepts welcome, and responds to bounded heartbeats', () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  socket.open();
  assert.deepEqual(socket.sent, [
    {
      type: 'authenticate',
      protocol_version: 1,
      token: configuration.token,
      backend_kind: 'thunderbird',
      backend_version: '153.5.0',
      connector_version: '0.2.0',
      capabilities: [],
    },
  ]);
  socket.receive(welcome);
  assert.equal(fixture.timers.size, 1);
  socket.receive(ping);
  socket.receive({ ...ping, sequence: 2 });
  assert.deepEqual(socket.sent.slice(1), [
    { ...ping, type: 'pong' },
    { ...ping, type: 'pong', sequence: 2 },
  ]);
  assert.equal(
    JSON.stringify(socket.sent.slice(1)).includes(configuration.token),
    false,
  );
  fixture.stop();
  assert.equal(fixture.timers.size, 0);
});

for (const message of [
  '{',
  ' '.repeat(65537),
  new Uint8Array([1]),
  { ...welcome, protocol_version: 2 },
  { ...welcome, heartbeat_timeout_ms: 99999 },
  { ...welcome, capabilities: ['mail'] },
  ping,
  { ...welcome, generation: 'bad' },
]) {
  test(`stops on invalid handshake ${String(message).slice(0, 30)}`, () => {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    socket.receive(message);
    assert.equal(socket.readyState, 3);
    assert.equal(fixture.timers.size, 0);
  });
}

test('rejects stale generation, duplicate ping, and out-of-order messages', () => {
  for (const message of [
    { ...ping, generation: 'c'.repeat(32) },
    welcome,
    { ...ping, sequence: 1 },
  ]) {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    socket.receive(welcome);
    socket.receive(ping);
    socket.receive(message);
    assert.equal(socket.readyState, 3);
    assert.equal(fixture.timers.size, 0);
  }
});

for (const code of [
  'authentication_failed',
  'incompatible_version',
  'session_replaced',
  'invalid_message',
]) {
  test(`stops on fatal server error ${code}`, () => {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    socket.receive({ type: 'error', protocol_version: 1, code });
    assert.equal(fixture.timers.size, 0);
  });
}

test('rejects a server error with a different active generation', () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  socket.open();
  socket.receive(welcome);
  socket.receive({
    type: 'error',
    protocol_version: 1,
    code: 'server_busy',
    generation: generation.replaceAll('b', 'c'),
  });
  assert.equal(fixture.timers.size, 0);
});
