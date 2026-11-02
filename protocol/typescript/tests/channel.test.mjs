import assert from 'node:assert/strict';
import { Buffer } from 'node:buffer';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

function built(path) {
  return import(pathToFileURL(resolve(process.env.RAICHO_PROTOCOL_BUILD_DIR, path)).href);
}

const { canonicalJson, createChannel, frameMac, sessionKey } = await built('channel.js');
const { serverKey } = await built('authentication.js');
const session = JSON.parse(
  await readFile(new URL('../../fixtures/authentication/session.json', import.meta.url), 'utf8'),
);
const authentication = JSON.parse(
  await readFile(new URL('../../fixtures/authentication/vector.json', import.meta.url), 'utf8'),
);

function bytes(text) {
  return Uint8Array.from(Buffer.from(text, 'hex'));
}

test('shared vector derives the session key and frame MACs from the token', async () => {
  const key = await sessionKey(await serverKey(authentication.token), session.transcript, session.generation);
  assert.equal(Buffer.from(key).toString('hex'), session.session_key);
  for (const frame of session.frames) {
    assert.equal(canonicalJson(frame.message), frame.canonical);
    assert.equal(await frameMac(key, frame.sender, frame.counter, frame.message), frame.mac);
  }
  for (const example of session.canonical) {
    assert.equal(canonicalJson(example.value), example.canonical);
  }
});

test('channels accept each frame once, in order, from the other peer', async () => {
  const key = bytes(session.session_key);
  const [ping, pong] = session.frames.map((frame) => JSON.stringify(frame.message));
  const client = createChannel(key, 'client');
  await client.open(ping, 'server_control', session.generation);
  await assert.rejects(client.open(ping, 'server_control', session.generation), { code: 'authentication_failed' });
  const server = createChannel(key, 'server');
  await server.open(pong, 'client_control', session.generation);
  await assert.rejects(
    createChannel(key, 'server').open(ping.replace('ping', 'pong'), 'client_control', session.generation),
    { code: 'authentication_failed' },
  );
  const sealing = createChannel(key, 'server');
  assert.deepEqual(JSON.parse(await sealing.seal(session.frames[0].message)), session.frames[0].message);
});

function sealedPings(key) {
  const sender = createChannel(key, 'server');
  const ping = session.frames[0].message;
  return Promise.all([sender.seal(ping), sender.seal({ ...ping, sequence: ping.sequence + 1 })]);
}

test('overlapping opens check consecutive frame counters', async () => {
  const key = bytes(session.session_key);
  const [first, second] = await sealedPings(key);
  const receiver = createChannel(key, 'client');
  await Promise.all([
    receiver.open(first, 'server_control', session.generation),
    receiver.open(second, 'server_control', session.generation),
  ]);
});

test('an overlapping duplicate frame fails and closes the channel', async () => {
  const key = bytes(session.session_key);
  const [first, second] = await sealedPings(key);
  const receiver = createChannel(key, 'client');
  const results = await Promise.allSettled([
    receiver.open(first, 'server_control', session.generation),
    receiver.open(first, 'server_control', session.generation),
  ]);
  assert.deepEqual(
    results.map(({ status }) => status),
    ['fulfilled', 'rejected'],
  );
  assert.equal(results[1].reason.code, 'authentication_failed');
  await assert.rejects(receiver.open(second, 'server_control', session.generation), { code: 'authentication_failed' });
  await assert.rejects(receiver.seal(session.frames[1].message), {
    code: 'authentication_failed',
  });
});

test('canonical JSON leaves out undefined members, as the wire encoding does', () => {
  const message = session.frames[0].message;
  assert.equal(canonicalJson({ ...message, extra: undefined }), canonicalJson(message));
});

test('a frame without a MAC is invalid', async () => {
  const receiver = createChannel(bytes(session.session_key), 'client');
  const challenge = JSON.stringify({
    type: 'challenge',
    protocol_version: 2,
    server_nonce: 'f'.repeat(64),
  });
  await assert.rejects(receiver.open(challenge, 'challenge', session.generation), { code: 'invalid_message' });
});
