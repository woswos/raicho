import assert from 'node:assert/strict';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { connectorFixture, generation, ping } from './connector_fixture.mjs';

const request = (requestId, operation = { name: 'list_accounts' }) => ({
  type: 'request',
  protocol_version: 2,
  generation,
  request_id: requestId,
  operation,
});

async function connected() {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  await socket.handshake();
  return { fixture, socket };
}

async function settled() {
  for (let turn = 0; turn < 100; turn += 1) await setImmediate();
}

// Sealing uses WebCrypto, so a reply arrives after several turns of the event loop.
async function opened(socket, index) {
  for (let turn = 0; turn < 100 && socket.sent.length <= index; turn += 1) await setImmediate();
  return socket.server.open(JSON.stringify(socket.sent[index]), 'client_control', generation);
}

test('a request is answered with a sealed reply while heartbeat continues', async () => {
  const { fixture, socket } = await connected();
  assert.equal(fixture.resets, 1);
  await socket.receiveSealed(request(7, { name: 'list_mailboxes', account: 'A'.repeat(22) }));
  assert.deepEqual(fixture.requests[0].operation, { name: 'list_mailboxes', account: 'A'.repeat(22) });
  await socket.receiveSealed(ping);
  const pong = await opened(socket, 1);
  assert.equal(pong.type, 'pong');
  fixture.requests[0].resolve({ kind: 'accounts', accounts: [] });
  const reply = await opened(socket, 2);
  assert.deepEqual(reply, {
    type: 'reply',
    protocol_version: 2,
    generation,
    request_id: 7,
    result: { kind: 'accounts', accounts: [] },
    mac: reply.mac,
  });
  fixture.stop();
});

test('replies keep frame order when Thunderbird answers out of order', async () => {
  const { fixture, socket } = await connected();
  await socket.receiveSealed(request(1));
  await socket.receiveSealed(request(2));
  fixture.requests[1].resolve({ kind: 'closed' });
  fixture.requests[0].resolve({ kind: 'error', code: 'stale_handle' });
  assert.equal((await opened(socket, 1)).request_id, 2);
  assert.equal((await opened(socket, 2)).request_id, 1);
  fixture.stop();
});

test('a cancelled request sends no reply and a new session resets the adapter', async () => {
  const { fixture, socket } = await connected();
  await socket.receiveSealed(request(3));
  await socket.receiveSealed({ type: 'cancel', protocol_version: 2, generation, request_id: 3 });
  fixture.requests[0].resolve({ kind: 'closed' });
  await settled();
  assert.equal(socket.sent.length, 1);
  socket.close();
  fixture.fireTimer(1000);
  await fixture.sockets[1].handshake();
  assert.equal(fixture.resets, 2);
  fixture.stop();
});

test('a reply for a closed connection is dropped', async () => {
  const { fixture, socket } = await connected();
  await socket.receiveSealed(request(4));
  socket.close();
  fixture.requests[0].resolve({ kind: 'closed' });
  await settled();
  assert.equal(socket.sent.length, 1);
  fixture.stop();
});
