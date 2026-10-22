import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';
import { TextEncoder } from 'node:util';

const { startProbeTransport } = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_MAIL_PROBE_BUILD_DIR, 'probe_transport.js'),
  ).href
);

test('a disconnect during send loses the result without replay on reconnect', async () => {
  const sockets = [];
  const timers = [];
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
    {
      connect() {
        const socket = {
          readyState: 1,
          sent: [],
          send(data) {
            this.sent.push(JSON.parse(data));
          },
          close(code = 1006) {
            this.readyState = 3;
            this.onclose({ code });
          },
        };
        sockets.push(socket);
        return socket;
      },
      schedule(callback) {
        timers.push(callback);
      },
    },
  );
  const command = new TextEncoder().encode(
    JSON.stringify({ id: 'send_once', action: 'send' }),
  ).buffer;
  sockets[0].onopen();
  sockets[0].onmessage({ data: command });
  sockets[0].close();
  finishSend({ mode: 'sendNow' });
  await setImmediate();
  timers.shift()();
  sockets[1].onopen();
  await setImmediate();
  assert.deepEqual(sockets[0].sent, [metadata]);
  assert.deepEqual(sockets[1].sent, [metadata]);
  assert.equal(attempts, 1);
  sockets[1].onmessage({ data: command });
  await setImmediate();
  assert.equal(sockets[1].sent[1].ok, false);
  assert.equal(attempts, 1);
  sockets[1].close(4003);
  assert.equal(timers.length, 0);
});
