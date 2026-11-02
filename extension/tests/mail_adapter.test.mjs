import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';
import { TextEncoder } from 'node:util';

function built(path) {
  return import(pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, path)).href);
}

const { createMailAdapter, RESULT_BUDGET_BYTES, PAGE_MESSAGES } = await built('extension/src/mail_adapter.js');
const { decodeFrame } = await built('protocol/typescript/src/decode_frame.js');
const { LIMITS } = await built('protocol/typescript/src/limits_generated.js');

function event() {
  const listeners = [];
  return {
    addListener: (listener) => listeners.push(listener),
    fire: async (...values) => {
      for (const listener of listeners) await listener(...values);
    },
  };
}

function header(id, changes = {}) {
  return {
    id,
    date: new Date(Date.UTC(2026, 10, 3, 8, 0, id % 60, 123)),
    author: `Zoë ${String(id)} <zoe@raicho.test>`,
    recipients: ['sender@raicho.test', 'alias@raicho.test'],
    subject: `Fictional ${String(id)}`,
    read: id % 2 === 0,
    flagged: false,
    ...changes,
  };
}

function thunderbird({ folders = [], messages = [] } = {}) {
  const lists = new Map();
  const aborted = [];
  let nextList = 0;
  const page = (remaining) => {
    const current = remaining.splice(0, 100);
    if (remaining.length === 0) return { id: null, messages: current };
    const id = `list-${String(++nextList)}`;
    lists.set(id, remaining);
    return { id, messages: current };
  };
  return {
    aborted,
    accounts: {
      list: async () => [
        {
          id: 'account1',
          name: 'Arbeit\u0007 Zürich',
          type: 'imap',
          identities: [
            { id: 'id1', name: 'Zoë', email: 'zoe@raicho.test' },
            { id: 'id2', name: 'No address', email: '' },
          ],
        },
      ],
      onDeleted: event(),
    },
    folders: {
      query: async (query) => {
        assert.deepEqual(query, {
          accountId: 'account1',
          isRoot: false,
          isUnified: false,
          isTag: false,
          isVirtual: false,
        });
        return folders.map((folder) => ({ ...folder }));
      },
      onRenamed: event(),
      onMoved: event(),
      onDeleted: event(),
    },
    messages: {
      list: async (folderId, options) => {
        assert.deepEqual(options, { sortType: 'date', sortOrder: 'descending' });
        if (!folders.some((folder) => folder.id === folderId)) throw new Error('Folder not found');
        return page([...messages]);
      },
      continueList: async (id) => {
        const remaining = lists.get(id);
        lists.delete(id);
        return page(remaining);
      },
      abortList: async (id) => {
        aborted.push(id);
        lists.delete(id);
      },
      onMoved: event(),
      onDeleted: event(),
    },
  };
}

function folder(path, specialUse) {
  return {
    id: `account1:/${path}`,
    accountId: 'account1',
    name: path.split('/').at(-1),
    path,
    ...(specialUse ? { specialUse } : {}),
  };
}

// Every result must fit a reply frame that both decoders accept.
function frame(result) {
  const raw = JSON.stringify({
    type: 'reply',
    protocol_version: 2,
    generation: 'b'.repeat(32),
    request_id: 2147483647,
    result,
    mac: 'a'.repeat(64),
  });
  assert.ok(new TextEncoder().encode(raw).byteLength <= LIMITS.maximum_control_bytes);
  decodeFrame(raw, 'client_control', 'b'.repeat(32));
  return result;
}

async function execute(adapter, operation) {
  return frame(await adapter.execute(operation));
}

test('accounts and identities receive transient handles and clean text', async () => {
  const adapter = createMailAdapter(thunderbird());
  const result = await execute(adapter, { name: 'list_accounts' });
  assert.equal(result.accounts[0].name, 'Arbeit  Zürich');
  assert.match(result.accounts[0].id, /^[A-Za-z0-9_-]{22}$/u);
  assert.deepEqual(
    result.accounts[0].identities.map((identity) => identity.email),
    ['zoe@raicho.test'],
  );
  const again = await execute(adapter, { name: 'list_accounts' });
  assert.equal(again.accounts[0].id, result.accounts[0].id);
  adapter.reset();
  assert.deepEqual(await execute(adapter, { name: 'list_mailboxes', account: result.accounts[0].id }), {
    kind: 'error',
    code: 'stale_handle',
  });
});

test('mailboxes keep their hierarchy and roles across pages', async () => {
  const folders = [folder('INBOX', ['inbox']), folder('Archives', ['archives']), folder('INBOX/Projects')];
  for (let index = 0; index < 220; index += 1) folders.push(folder(`Many/${String(index).padStart(3, '0')}`));
  const adapter = createMailAdapter(thunderbird({ folders }));
  const { accounts } = await adapter.execute({ name: 'list_accounts' });
  const first = await execute(adapter, { name: 'list_mailboxes', account: accounts[0].id });
  assert.equal(first.mailboxes.length, 200);
  assert.equal(first.mailboxes[0].name, 'Archives');
  assert.equal(first.mailboxes[0].role, 'archive');
  const inbox = first.mailboxes.find((mailbox) => mailbox.role === 'inbox');
  assert.equal(first.mailboxes.find((mailbox) => mailbox.name === 'Projects').parent, inbox.id);
  const second = await execute(adapter, { name: 'continue_list', cursor: first.cursor });
  assert.equal(second.mailboxes.length, 23);
  assert.equal(second.cursor, undefined);
  assert.deepEqual(await adapter.execute({ name: 'continue_list', cursor: first.cursor }), {
    kind: 'error',
    code: 'stale_cursor',
  });
});

async function openMailbox(api) {
  const adapter = createMailAdapter(api);
  const { accounts } = await adapter.execute({ name: 'list_accounts' });
  const { mailboxes } = await adapter.execute({ name: 'list_mailboxes', account: accounts[0].id });
  return { adapter, mailbox: mailboxes[0].id };
}

test('summaries are paginated, bounded, and converted without milliseconds', async () => {
  const api = thunderbird({
    folders: [folder('INBOX', ['inbox'])],
    messages: Array.from({ length: 130 }, (_, index) => header(index + 1)),
  });
  const { adapter, mailbox } = await openMailbox(api);
  const first = await execute(adapter, { name: 'list_messages', mailbox });
  assert.equal(first.messages.length, PAGE_MESSAGES);
  assert.deepEqual(
    { ...first.messages[0], id: '' },
    {
      id: '',
      subject: 'Fictional 1',
      author: 'Zoë 1 <zoe@raicho.test>',
      recipients: 'sender@raicho.test, alias@raicho.test',
      date: '2026-11-03T08:00:01Z',
      read: false,
      flagged: false,
    },
  );
  const pages = [first];
  while (pages.at(-1).cursor) {
    pages.push(await execute(adapter, { name: 'continue_list', cursor: pages.at(-1).cursor }));
  }
  assert.deepEqual(
    pages.map((page) => page.messages.length),
    [50, 50, 30],
  );
  assert.equal(new Set(pages.flatMap((page) => page.messages.map((message) => message.id))).size, 130);
});

test('long Unicode text is cut by code point and pages stay within the byte budget', async () => {
  const api = thunderbird({
    folders: [folder('INBOX', ['inbox'])],
    messages: Array.from({ length: 60 }, (_, index) =>
      header(index + 1, {
        subject: `\ud800${'🐦'.repeat(400)}`,
        author: '雷'.repeat(400),
        recipients: ['\n'.repeat(400)],
        date: new Date(Number.NaN),
      }),
    ),
  });
  const { adapter, mailbox } = await openMailbox(api);
  const page = await execute(adapter, { name: 'list_messages', mailbox });
  assert.ok(page.messages.length < PAGE_MESSAGES);
  assert.ok(new TextEncoder().encode(JSON.stringify(page)).byteLength <= RESULT_BUDGET_BYTES);
  const [summary] = page.messages;
  assert.equal(Array.from(summary.subject).length, 300);
  assert.equal(summary.subject[0], '�');
  assert.equal(summary.recipients, ' '.repeat(300));
  assert.equal(summary.date, '1970-01-01T00:00:00Z');
});

test('moved messages disappear from later pages and folder changes make handles stale', async () => {
  const api = thunderbird({
    folders: [folder('INBOX', ['inbox']), folder('INBOX/Projects')],
    messages: Array.from({ length: 250 }, (_, index) => header(index + 1)),
  });
  const { adapter, mailbox } = await openMailbox(api);
  const first = await adapter.execute({ name: 'list_messages', mailbox });
  await api.messages.onMoved.fire({ id: null, messages: [header(51), header(52)] }, { id: null, messages: [] });
  const second = await adapter.execute({ name: 'continue_list', cursor: first.cursor });
  assert.equal(second.messages[0].subject, 'Fictional 53');

  await api.folders.onRenamed.fire(folder('INBOX'), folder('Renamed'));
  assert.deepEqual(await adapter.execute({ name: 'list_messages', mailbox }), { kind: 'error', code: 'stale_handle' });
  assert.deepEqual(await adapter.execute({ name: 'continue_list', cursor: second.cursor }), {
    kind: 'error',
    code: 'stale_cursor',
  });
  assert.ok(api.aborted.length > 0);
});

test('closing, idle expiry, and account deletion end lists and handles', async () => {
  let now = 0;
  const api = thunderbird({
    folders: [folder('INBOX', ['inbox'])],
    messages: Array.from({ length: 250 }, (_, index) => header(index + 1)),
  });
  const adapter = createMailAdapter(api, () => now);
  const { accounts } = await adapter.execute({ name: 'list_accounts' });
  const { mailboxes } = await adapter.execute({ name: 'list_mailboxes', account: accounts[0].id });
  const first = await adapter.execute({ name: 'list_messages', mailbox: mailboxes[0].id });
  assert.deepEqual(await adapter.execute({ name: 'close_list', cursor: first.cursor }), { kind: 'closed' });
  assert.deepEqual(api.aborted, ['list-1']);

  const second = await adapter.execute({ name: 'list_messages', mailbox: mailboxes[0].id });
  now = LIMITS.list_idle_timeout_ms;
  assert.deepEqual(await adapter.execute({ name: 'continue_list', cursor: second.cursor }), {
    kind: 'error',
    code: 'stale_cursor',
  });
  assert.equal(api.aborted.length, 2);

  await api.accounts.onDeleted.fire('account1');
  assert.deepEqual(await adapter.execute({ name: 'list_mailboxes', account: accounts[0].id }), {
    kind: 'error',
    code: 'stale_handle',
  });
});

test('Thunderbird failures become categorized errors', async () => {
  const api = thunderbird();
  api.accounts.list = async () => {
    throw new Error('Private Thunderbird detail');
  };
  const adapter = createMailAdapter(api);
  assert.deepEqual(await adapter.execute({ name: 'list_accounts' }), { kind: 'error', code: 'failed' });
  assert.deepEqual(await adapter.execute({ name: 'list_messages', mailbox: 'A'.repeat(22) }), {
    kind: 'error',
    code: 'stale_handle',
  });
});
