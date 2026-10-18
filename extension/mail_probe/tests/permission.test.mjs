import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL, URL } from 'node:url';

const manifest = JSON.parse(
  await readFile(new URL('../manifest.json', import.meta.url)),
);

test('background send is optional-only and never requested at installation', () => {
  assert.deepEqual(manifest.optional_permissions, ['messages.send']);
  assert.equal(manifest.permissions.includes('messages.send'), false);
  assert.equal(manifest.permissions.includes('mailTabs'), false);
  assert.equal(manifest.options_ui.page, 'permission.html');
});

test('send permission is requested synchronously only inside the button gesture', async () => {
  const { installPermissionPrompt } = await import(
    pathToFileURL(
      resolve(process.env.RAICHO_MAIL_PROBE_BUILD_DIR, 'permission_prompt.js'),
    ).href
  );
  let click;
  const requests = [];
  const button = {
    disabled: false,
    addEventListener(name, listener) {
      assert.equal(name, 'click');
      click = listener;
    },
  };
  const status = { textContent: '' };
  installPermissionPrompt(button, status, {
    request(request) {
      requests.push(request);
      return Promise.resolve(true);
    },
  });
  assert.equal(requests.length, 0);
  click();
  assert.deepEqual(requests, [{ permissions: ['messages.send'] }]);
  await setImmediate();
  assert.equal(
    status.textContent,
    'Background sending is allowed for this fictional-mail probe.',
  );
});
