import assert from 'node:assert/strict';
import { test } from 'node:test';
import { connectorFixture, ping, welcome } from './connector_fixture.mjs';

test('uses bounded exponential retry for connection and handshake timeouts', () => {
  const fixture = connectorFixture();
  for (const [attempt, delay] of [
    1000, 2000, 4000, 8000, 16000, 30000, 30000,
  ].entries()) {
    if (attempt % 2 !== 0) fixture.sockets.at(-1).open();
    fixture.fireTimer(5000);
    assert.equal(fixture.timers.size, 1);
    fixture.fireTimer(delay);
  }
  fixture.stop();
});

test('adds jitter and resets backoff only after a valid heartbeat', () => {
  const fixture = connectorFixture();
  fixture.dependencies.random = () => 0.5;
  fixture.fireTimer(5000);
  fixture.fireTimer(1500);
  const socket = fixture.sockets[1];
  socket.open();
  socket.receive(welcome);
  socket.close();
  fixture.fireTimer(3000);
  const active = fixture.sockets[2];
  active.open();
  active.receive(welcome);
  active.receive(ping);
  active.close();
  fixture.fireTimer(1500);
  fixture.stop();
});

test('drops a silent peer and ignores every captured stale socket callback', () => {
  const fixture = connectorFixture();
  const first = fixture.sockets[0];
  first.open();
  first.receive(welcome);
  const stale = {
    open: first.onopen,
    close: first.onclose,
    error: first.onerror,
    message: first.onmessage,
  };
  fixture.fireTimer(45000);
  fixture.fireTimer(1000);
  const second = fixture.sockets[1];
  second.open();
  second.receive(welcome);
  stale.open();
  stale.close({ code: 4001 });
  stale.error();
  stale.message({ data: JSON.stringify(ping) });
  assert.equal(second.sent.length, 1);
  assert.equal(second.readyState, 1);
  second.receive(ping);
  assert.equal(second.sent.length, 2);
  fixture.stop();
});

for (const code of [4001, 4002, 4003]) {
  test(`stops after close ${code} without retrying`, () => {
    const fixture = connectorFixture();
    fixture.sockets[0].onclose({ code });
    assert.equal(fixture.timers.size, 0);
  });
}

test('retries server busy and heartbeat timeout without an application queue', () => {
  for (const code of ['server_busy', 'heartbeat_timeout']) {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    socket.receive({ type: 'error', protocol_version: 1, code });
    fixture.fireTimer(1000);
    fixture.stop();
  }
});

test('closes congested senders and handles connection and send failures', () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  socket.open();
  socket.receive(welcome);
  socket.bufferedAmount = 1;
  socket.receive(ping);
  assert.equal(socket.readyState, 3);
  fixture.dependencies.connect = () => {
    throw new Error('Private endpoint');
  };
  fixture.fireTimer(1000);
  fixture.fireTimer(2000);
  assert.equal(fixture.timers.size, 1);
  fixture.stop();
  const failed = connectorFixture();
  failed.sockets[0].send = () => {
    throw new Error('Private data');
  };
  failed.sockets[0].open();
  assert.equal(failed.timers.size, 1);
  failed.stop();
});
