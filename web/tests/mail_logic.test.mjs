import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const load = (name) => import(pathToFileURL(resolve(outputDirectory, name)).href);
const { mailboxTree } = await load('mailbox_tree.js');
const { appendSummaries, longDate, shortDate } = await load('summaries.js');
const { failureMessage, failureState } = await load('failures.js');

test('special mailboxes come first and children follow their parents', () => {
  const tree = mailboxTree([
    { id: 'p', name: 'Projekte' },
    { id: 't', name: 'Trash', role: 'trash' },
    { id: 'c', name: 'Client', parent: 'p' },
    { id: 'i', name: 'Inbox', role: 'inbox' },
    { id: 'a', name: 'Alpha', parent: 'p' },
    { id: 'o', name: 'Orphan', parent: 'missing' },
  ]);
  assert.deepEqual(
    tree.map(({ mailbox, depth }) => `${String(depth)}:${mailbox.name}`),
    ['0:Inbox', '0:Trash', '0:Orphan', '0:Projekte', '1:Alpha', '1:Client'],
  );
});

test('a parent cycle cannot hide mailboxes or loop', () => {
  const tree = mailboxTree([
    { id: 'a', name: 'A', parent: 'b' },
    { id: 'b', name: 'B', parent: 'a' },
  ]);
  assert.deepEqual(
    tree.map(({ mailbox, depth }) => `${String(depth)}:${mailbox.name}`),
    ['0:A', '1:B'],
  );
});

test('later pages add only new summaries', () => {
  const summary = (id) => ({
    id,
    subject: id,
    author: '',
    recipients: '',
    date: '2026-11-03T08:00:00Z',
    read: true,
    flagged: false,
  });
  assert.deepEqual(
    appendSummaries([summary('a'), summary('b')], [summary('b'), summary('c')]).map((item) => item.id),
    ['a', 'b', 'c'],
  );
});

test('dates show the time today, the day this year, and the year otherwise', () => {
  const now = new Date('2026-11-03T15:00:00');
  assert.equal(shortDate(new Date('2026-11-03T09:05:00').toISOString(), now, 'en-GB'), '09:05');
  assert.equal(shortDate(new Date('2026-10-01T09:05:00').toISOString(), now, 'en-GB'), '1 Oct');
  assert.equal(shortDate(new Date('2025-10-01T09:05:00').toISOString(), now, 'en-GB'), '1 Oct 2025');
  assert.equal(shortDate('1970-01-01T00:00:00Z', now, 'en-GB'), '');
  assert.equal(longDate('1970-01-01T00:00:00Z', 'en-GB'), '');
  assert.match(longDate('2026-11-03T08:00:00Z', 'en-GB'), /2026/u);
});

test('failures map to the state the interface shows', () => {
  for (const [failure, state] of [
    [{ kind: 'api', code: 'unauthenticated' }, 'unauthenticated'],
    [{ kind: 'api', code: 'stale_handle' }, 'stale'],
    [{ kind: 'api', code: 'stale_cursor' }, 'stale'],
    [{ kind: 'api', code: 'backend_disconnected' }, 'disconnected'],
    [{ kind: 'api', code: 'backend_busy' }, 'error'],
    [{ kind: 'timeout' }, 'error'],
  ]) {
    assert.equal(failureState(failure), state, JSON.stringify(failure));
  }
  const codes = [
    'unauthenticated',
    'forbidden_origin',
    'invalid_request',
    'rate_limited',
    'invalid_password',
    'login_unconfigured',
    'storage_unavailable',
    'backend_disconnected',
    'backend_busy',
    'backend_timeout',
    'stale_handle',
    'stale_cursor',
    'unsupported',
    'backend_failed',
  ];
  const messages = codes.map((code) => failureMessage({ kind: 'api', code }));
  assert.ok(messages.every((message) => typeof message === 'string' && message.length > 10));
  for (const kind of ['network', 'timeout', 'invalid']) {
    assert.ok(failureMessage({ kind }).length > 10);
  }
});
