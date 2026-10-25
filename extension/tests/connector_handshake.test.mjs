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
      authentication.authenticationMessage(
        challenge.server_nonce,
        authenticate,
      ),
    ),
  );
  await socket.receive(await provenWelcome(authenticate));
  assert.equal(fixture.timers.size, 1);
  await socket.receive(ping);
  await socket.receive({ ...ping, sequence: 2 });
  assert.deepEqual(socket.sent.slice(1), [
    { ...ping, type: 'pong' },
    { ...ping, type: 'pong', sequence: 2 },
  ]);
  assert.equal(
    JSON.stringify(socket.sent).includes(configuration.token),
    false,
  );
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
  [
    'forged signature',
    (message) => ({ ...message, server_signature: 'e'.repeat(64) }),
  ],
  [
    'another protocol version',
    (message) => ({ ...message, protocol_version: 2 }),
  ],
  [
    'unsupported heartbeat',
    (message) => ({ ...message, heartbeat_timeout_ms: 99999 }),
  ],
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
  'session_replaced',
  'invalid_message',
]) {
  test(`retries unproven error ${code} but stops on it after proof`, async () => {
    const unproven = connectorFixture();
    const pending = unproven.sockets[0];
    pending.open();
    await pending.receive(challenge);
    await pending.receive({ type: 'error', protocol_version: 1, code });
    await assertRetried(unproven, pending);
    const proven = connectorFixture();
    const socket = proven.sockets[0];
    await socket.handshake();
    await socket.receive({
      type: 'error',
      protocol_version: 1,
      code,
      generation,
    });
    assert.equal(proven.timers.size, 0);
  });
}

test('stops on stale generation, duplicate ping, and out-of-order messages after proof', async () => {
  for (const message of [
    { ...ping, generation: 'c'.repeat(32) },
    welcome,
    { ...ping, sequence: 1 },
    {
      type: 'error',
      protocol_version: 1,
      code: 'server_busy',
      generation: generation.replaceAll('b', 'c'),
    },
  ]) {
    const fixture = connectorFixture();
    const socket = fixture.sockets[0];
    await socket.handshake();
    await socket.receive(ping);
    await socket.receive(message);
    assert.equal(socket.readyState, 3);
    assert.equal(fixture.timers.size, 0);
  }
});
