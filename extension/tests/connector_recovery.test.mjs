import assert from 'node:assert/strict';
import { test } from 'node:test';
import { challenge, connectorFixture, generation, ping } from './connector_fixture.mjs';

test('uses bounded exponential retry for connection and handshake timeouts', () => {
  const fixture = connectorFixture();
  for (const [opens, delay] of [
    [false, 1000],
    [true, 2000],
    [false, 4000],
    [true, 8000],
    [false, 16000],
    [true, 30000],
    [false, 30000],
  ]) {
    if (opens) fixture.sockets.at(-1).open();
    fixture.fireTimer(5000);
    assert.equal(fixture.timers.size, 1);
    fixture.fireTimer(delay);
  }
  fixture.stop();
});

test('adds jitter and resets backoff only after a valid heartbeat', async () => {
  const fixture = connectorFixture();
  fixture.dependencies.random = () => 0.5;
  fixture.fireTimer(5000);
  fixture.fireTimer(1500);
  const socket = fixture.sockets[1];
  await socket.handshake();
  socket.close();
  fixture.fireTimer(3000);
  const active = fixture.sockets[2];
  await active.handshake();
  await active.receiveSealed(ping);
  active.close();
  fixture.fireTimer(1500);
  fixture.stop();
});

test('drops a silent peer and ignores every captured stale socket callback', async () => {
  const fixture = connectorFixture();
  const first = fixture.sockets[0];
  await first.handshake();
  const stale = {
    open: first.onopen,
    close: first.onclose,
    error: first.onerror,
    message: first.onmessage,
  };
  fixture.fireTimer(45000);
  fixture.fireTimer(1000);
  const second = fixture.sockets[1];
  await second.handshake();
  stale.open?.();
  stale.close({ code: 4001 });
  stale.error();
  await stale.message({ data: JSON.stringify(ping) });
  assert.equal(second.sent.length, 1);
  assert.equal(second.readyState, 1);
  await second.receiveSealed(ping);
  assert.equal(second.sent.length, 2);
  fixture.stop();
});

for (const code of [4001, 4002, 4003]) {
  test(`retries close ${code} before and after proof`, async () => {
    const unproven = connectorFixture();
    unproven.sockets[0].onclose({ code });
    assert.equal(unproven.timers.size, 1);
    const proven = connectorFixture();
    await proven.sockets[0].handshake();
    proven.sockets[0].onclose({ code });
    assert.equal(proven.timers.size, 1);
    assert.equal(proven.sockets.length, 1);
  });
}

test('retries server busy and heartbeat timeout without an application queue', async () => {
  for (const code of ['server_busy', 'heartbeat_timeout']) {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    await socket.handshake();
    await socket.receiveSealed({
      type: 'error',
      protocol_version: 1,
      code,
      generation,
    });
    fixture.fireTimer(1000);
    fixture.stop();
  }
});

test('closes congested senders and handles connection and send failures', async () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  await socket.handshake();
  socket.bufferedAmount = 1;
  await socket.receiveSealed(ping);
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
  await failed.sockets[0].receive(challenge);
  assert.equal(failed.timers.size, 1);
  assert.equal(failed.sockets[0].readyState, 3);
  failed.stop();
});
