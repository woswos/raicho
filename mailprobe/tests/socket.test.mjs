import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';
import { TextEncoder } from 'node:util';

import { probeFixture } from '../../extension/tests/probe_fixture.mjs';

const { startProbeTransport } = await import(
  pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'mailprobe/src/probe_transport.js')).href
);

test('a disconnect during send loses the result without replay on reconnect', async () => {
  const fixture = probeFixture();
  let finishSend;
  let attempts = 0;
  const metadata = {
    type: 'mail_probe',
    token: 'fixture',
    session_id: 'session',
  };
  startProbeTransport(
    'ws://probe/mail',
    metadata,
    () => {
      attempts++;
      return new Promise((resolve) => {
        finishSend = resolve;
      });
    },
    fixture.dependencies,
  );
  const command = new TextEncoder().encode(JSON.stringify({ id: 'send_once', action: 'send' })).buffer;
  const [first] = fixture.sockets;
  first.open();
  first.onmessage({ data: command });
  first.close();
  finishSend({ mode: 'sendNow' });
  await setImmediate();
  fixture.fireTimer(1000);
  const second = fixture.sockets[1];
  second.open();
  await setImmediate();
  assert.deepEqual(first.sent, [metadata]);
  assert.deepEqual(second.sent, [metadata]);
  assert.equal(attempts, 1);
  second.onmessage({ data: command });
  await setImmediate();
  assert.equal(second.sent[1].ok, false);
  assert.equal(attempts, 1);
});
