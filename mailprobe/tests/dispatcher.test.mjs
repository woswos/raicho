import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const { dispatchCommand } = await import(
  pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'mailprobe/src/dispatcher.js')).href
);

test('send requires an explicit mode and forwards the selected identity once', async () => {
  const calls = [];
  const api = {
    messages: {
      sendMessage(details, options) {
        calls.push({ details, options });
        return Promise.resolve({ mode: options.mode });
      },
    },
  };
  const details = {
    subject: 'fixture',
    identityId: 'secondary',
    plainTextBody: 'fictional body',
  };
  await assert.rejects(dispatchCommand(api, { action: 'send', arguments: { details } }));
  assert.equal(calls.length, 0);
  assert.deepEqual(
    await dispatchCommand(api, {
      action: 'send',
      arguments: { details, mode: 'sendLater' },
    }),
    { mode: 'sendLater' },
  );
  assert.deepEqual(calls, [{ details, options: { mode: 'sendLater' } }]);
});

test('begin-new records actual compose type without claiming draft replacement', async () => {
  const api = {
    compose: {
      beginNew: () => Promise.resolve({ id: 17 }),
      getComposeDetails: () => Promise.resolve({ type: 'new' }),
    },
  };
  assert.deepEqual(
    await dispatchCommand(api, {
      action: 'begin_new',
      arguments: { message_id: 3 },
    }),
    { tab: { id: 17 }, details: { type: 'new' } },
  );
});

test('folder selection uses the supported MV2 mail-tab update', async () => {
  const updates = [];
  const api = {
    mailTabs: {
      query: () => Promise.resolve([{ id: 4 }]),
      update(tabIdentifier, properties) {
        updates.push({ tabIdentifier, properties });
        return Promise.resolve({ id: tabIdentifier, ...properties });
      },
    },
  };
  assert.deepEqual(
    await dispatchCommand(api, {
      action: 'select_folder',
      arguments: { folder_id: 'account1://Drafts' },
    }),
    { tab: { id: 4, displayedFolder: 'account1://Drafts', folderMode: 'all' } },
  );
  assert.deepEqual(updates, [
    {
      tabIdentifier: 4,
      properties: { displayedFolder: 'account1://Drafts', folderMode: 'all' },
    },
  ]);
});

test('folder creation goes through Thunderbird', async () => {
  const created = [];
  const api = {
    folders: {
      create(parentIdentifier, name) {
        created.push({ parentIdentifier, name });
        return Promise.resolve({ id: `${parentIdentifier}${name}` });
      },
    },
  };
  assert.deepEqual(
    await dispatchCommand(api, {
      action: 'create_folder',
      arguments: { parent_id: 'account1://', name: 'Projects' },
    }),
    { id: 'account1://Projects' },
  );
  assert.deepEqual(created, [{ parentIdentifier: 'account1://', name: 'Projects' }]);
});
