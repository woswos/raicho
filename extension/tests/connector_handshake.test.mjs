import assert from 'node:assert/strict';
import { test } from 'node:test';
import {
  authentication,
  challenge,
  configuration,
  connectorFixture,
  generation,
  ping,
  provenWelcome,
  serverChannel,
  welcome,
} from './connector_fixture.mjs';

test('answers the challenge with a proof, never the token, and accepts a proven welcome', async () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  socket.open();
  assert.deepEqual(socket.sent, []);
  await socket.receive(challenge);
  const [authenticate] = socket.sent;
  assert.match(authenticate.client_nonce, /^[a-f0-9]{64}$/u);
  assert.deepEqual(
    { ...authenticate, client_nonce: '', client_proof: '' },
    {
      type: 'authenticate',
      protocol_version: 1,
      backend_kind: 'thunderbird',
      backend_version: '153.5.0',
      connector_version: '0.2.0',
      capabilities: [],
      client_nonce: '',
      client_proof: '',
    },
  );
  assert.equal(
    authenticate.client_proof,
    await authentication.clientProof(
      configuration.token,
      authentication.authenticationMessage(challenge.server_nonce, authenticate),
    ),
  );
  await socket.receive(await provenWelcome(authenticate));
  assert.equal(fixture.timers.size, 1);
  const server = await serverChannel(authenticate);
  await socket.receive(await server.seal(ping));
  await socket.receive(await server.seal({ ...ping, sequence: 2 }));
  const pongs = socket.sent.slice(1);
  assert.equal(pongs.length, 2);
  for (const [index, pong] of pongs.entries()) {
    assert.deepEqual(await server.open(JSON.stringify(pong), 'client_control', generation), {
      ...ping,
      type: 'pong',
      sequence: index + 1,
      mac: pong.mac,
    });
  }
  assert.equal(JSON.stringify(socket.sent).includes(configuration.token), false);
  fixture.stop();
  assert.equal(fixture.timers.size, 0);
});

async function assertRetried(fixture, socket) {
  assert.equal(socket.readyState, 3);
  assert.equal(fixture.timers.size, 1);
  assert.equal([...fixture.timers.values()][0].delay, 1000);
}

for (const message of [
  '{',
  new Uint8Array([1]),
  welcome,
  ping,
  { type: 'error', protocol_version: 1, code: 'authentication_failed' },
]) {
  test(`retries an unproven server before its challenge: ${String(message).slice(0, 20)}`, async () => {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    await socket.receive(message);
    await assertRetried(fixture, socket);
  });
}

for (const [name, change] of [
  ['forged signature', (message) => ({ ...message, server_signature: 'e'.repeat(64) })],
  ['another protocol version', (message) => ({ ...message, protocol_version: 2 })],
  ['removed heartbeat field', (message) => ({ ...message, heartbeat_timeout_ms: 45000 })],
  ['mail capability', (message) => ({ ...message, capabilities: ['mail'] })],
  ['invalid generation', (message) => ({ ...message, generation: 'bad' })],
]) {
  test(`retries an unproven welcome with a ${name}`, async () => {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    socket.open();
    await socket.receive(challenge);
    await socket.receive(change(await provenWelcome(socket.sent[0])));
    await assertRetried(fixture, socket);
  });
}

test('a welcome signed with another token is not trusted', async () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  socket.open();
  await socket.receive(challenge);
  await socket.receive(await provenWelcome(socket.sent[0], 'c'.repeat(64)));
  await assertRetried(fixture, socket);
});

for (const code of [
  'authentication_failed',
  'incompatible_version',
  'invalid_message',
  'server_busy',
  'heartbeat_timeout',
]) {
  test(`retries after an authenticated ${code} error`, async () => {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    await socket.handshake();
    await socket.receiveSealed({
      type: 'error',
      protocol_version: 1,
      code,
      generation,
    });
    await assertRetried(fixture, socket);
  });
}

test('retries an unproven replacement but stops on an authenticated one', async () => {
  const unproven = connectorFixture();
  const pending = unproven.sockets[0];
  pending.open();
  await pending.receive(challenge);
  await pending.receive({
    type: 'error',
    protocol_version: 1,
    code: 'session_replaced',
  });
  await assertRetried(unproven, pending);
  const proven = connectorFixture();
  const socket = proven.sockets[0];
  await socket.handshake();
  await socket.receiveSealed({
    type: 'error',
    protocol_version: 1,
    code: 'session_replaced',
    generation,
  });
  assert.equal(socket.readyState, 3);
  assert.equal(proven.timers.size, 0);
});

test('retries every frame it cannot authenticate after proof', async () => {
  for (const deliver of [
    (socket) => socket.receive({ ...ping, sequence: 2, mac: 'a'.repeat(64) }),
    (socket) => socket.receive({ ...ping, sequence: 2 }),
    (socket) => socket.receiveSealed({ ...ping, generation: 'c'.repeat(32) }),
    (socket) => socket.receive(welcome),
    (socket) => socket.receiveSealed({ ...ping, sequence: 1 }),
    (socket) =>
      socket.receiveSealed({
        type: 'error',
        protocol_version: 1,
        code: 'session_replaced',
        generation: 'c'.repeat(32),
      }),
  ]) {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    await socket.handshake();
    await socket.receiveSealed(ping);
    await deliver(socket);
    await assertRetried(fixture, socket);
  }
});

test('retries a replayed ping', async () => {
  const fixture = connectorFixture();
  const socket = fixture.sockets[0];
  await socket.handshake();
  const sealed = await socket.server.seal(ping);
  await socket.receive(sealed);
  await socket.receive(sealed);
  await assertRetried(fixture, socket);
});
