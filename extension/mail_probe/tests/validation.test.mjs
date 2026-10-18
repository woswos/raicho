import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const { parseCommand, parseConfiguration, messageDetails } = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_MAIL_PROBE_BUILD_DIR, 'validation.js'),
  ).href
);

test('accepts a finite command with a caller-owned identity', () => {
  assert.deepEqual(parseCommand({ id: 'first', action: 'inventory' }), {
    id: 'first',
    action: 'inventory',
    arguments: {},
  });
  assert.throws(() => parseCommand({ id: 'first', action: 'execute' }));
  assert.throws(() => parseCommand({ id: '', action: 'inventory' }));
  assert.throws(() =>
    parseCommand({ id: 'first', action: 'inventory', arguments: [] }),
  );
});

test('configuration accepts only fixture websocket endpoints and a token', () => {
  const token = 'a'.repeat(64);
  assert.deepEqual(
    parseConfiguration({ endpoint: 'ws://probe:8765/mail', token }),
    { endpoint: 'ws://probe:8765/mail', token },
  );
  assert.throws(() =>
    parseConfiguration({ endpoint: 'ws://user:secret@probe/mail', token }),
  );
  assert.throws(() =>
    parseConfiguration({ endpoint: 'ws://probe/mail?secret=value', token }),
  );
  assert.throws(() =>
    parseConfiguration({ endpoint: 'https://probe/mail', token }),
  );
  assert.throws(() =>
    parseConfiguration({ endpoint: 'ws://probe/mail', token: 'short' }),
  );
});

test('mail inputs retain invalid identity and recipient values for API probing', () => {
  assert.deepEqual(
    messageDetails({ subject: 'fixture', identityId: 'missing', to: [] }),
    { subject: 'fixture', identityId: 'missing', to: [] },
  );
  assert.throws(() => messageDetails({ subject: 123 }));
  assert.throws(() =>
    messageDetails({ subject: 'fixture', unsupported: true }),
  );
  assert.throws(() =>
    messageDetails({
      subject: 'fixture',
      attachments: [{ name: '../secret', content: 'data' }],
    }),
  );
});

test('small attachment inputs become File objects without path access', async () => {
  const details = messageDetails({
    subject: 'fixture',
    attachments: [
      { name: 'sample.txt', content: 'attachment content', type: 'text/plain' },
    ],
  });
  assert.equal(details.attachments[0].file.name, 'sample.txt');
  assert.equal(details.attachments[0].file.type, 'text/plain');
  assert.equal(await details.attachments[0].file.text(), 'attachment content');
  assert.throws(() =>
    messageDetails({
      subject: 'fixture',
      attachments: [{ name: 'sample.txt', content: 'a'.repeat(16385) }],
    }),
  );
});
