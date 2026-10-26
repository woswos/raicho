import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const {
  authenticationMessage,
  clientProof,
  randomNonce,
  serverSignature,
  verifyServerSignature,
} = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_PROTOCOL_BUILD_DIR, 'authentication.js'),
  ).href
);
const vector = JSON.parse(
  await readFile(
    new URL('../../fixtures/authentication/vector.json', import.meta.url),
    'utf8',
  ),
);

test('shared vector produces the same message, proof, and signature', async () => {
  const message = authenticationMessage(vector.server_nonce, vector);
  assert.equal(message, vector.message);
  assert.equal(await clientProof(vector.token, message), vector.client_proof);
  assert.equal(
    await serverSignature(vector.token, message),
    vector.server_signature,
  );
});

test('another token or message changes the proof and signature', async () => {
  const other = 'f'.repeat(64);
  assert.notEqual(
    await clientProof(other, vector.message),
    vector.client_proof,
  );
  assert.notEqual(
    await serverSignature(vector.token, `${vector.message}\n`),
    vector.server_signature,
  );
});

test('nonces are fresh lowercase hexadecimal', () => {
  const first = randomNonce();
  assert.match(first, /^[a-f0-9]{64}$/u);
  assert.notEqual(first, randomNonce());
});

test('server signatures verify only for the matching token and message', async () => {
  const { message, server_signature: signature, token } = vector;
  assert.equal(await verifyServerSignature(token, message, signature), true);
  assert.equal(
    await verifyServerSignature(token, `${message}\n`, signature),
    false,
  );
  assert.equal(
    await verifyServerSignature(token, message, signature.slice(1)),
    false,
  );
});
