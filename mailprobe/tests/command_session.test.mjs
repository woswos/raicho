import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const { CommandSession } = await import(
  pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'mailprobe/src/command_session.js')).href
);

test('executes a command once and rejects repeated identifiers', async () => {
  const commands = [];
  const session = new CommandSession(async (command) => {
    commands.push(command);
    return 'sent';
  });
  const command = { id: 'send_once', action: 'send', arguments: {} };
  assert.deepEqual(await session.execute(command), {
    type: 'result',
    id: 'send_once',
    ok: true,
    result: 'sent',
  });
  assert.equal((await session.execute(command)).ok, false);
  assert.equal(commands.length, 1);
});

test('an API rejection is reported without retry', async () => {
  let attempts = 0;
  const session = new CommandSession(() => {
    attempts++;
    return Promise.reject(new Error('SMTP refused fixture'));
  });
  assert.deepEqual(await session.execute({ id: 'failure', action: 'send' }), {
    type: 'result',
    id: 'failure',
    ok: false,
    error: 'SMTP refused fixture',
  });
  assert.equal(attempts, 1);
});

test('lost acknowledgments do not create replay state', async () => {
  let attempts = 0;
  const session = new CommandSession(async () => {
    attempts++;
    return 'submitted';
  });
  await session.execute({ id: 'lost', action: 'send' });
  await session.execute({ id: 'inventory', action: 'inventory' });
  assert.equal(attempts, 2);
  assert.equal((await session.execute({ id: 'lost', action: 'send' })).ok, false);
  assert.equal(attempts, 2);
});

test('malformed commands fail without invocation', async () => {
  const session = new CommandSession(async () => {
    throw new Error('Should not execute');
  });
  assert.equal((await session.execute({ id: 'invalid', action: 'unknown' })).ok, false);
});

test('oversized results fail after a single invocation', async () => {
  const session = new CommandSession(async () => 'a'.repeat(60001));
  const result = await session.execute({
    id: 'oversized',
    action: 'inventory',
  });
  assert.equal(result.ok, false);
  assert.equal(result.error, 'Probe result exceeds the fixture limit.');
});
