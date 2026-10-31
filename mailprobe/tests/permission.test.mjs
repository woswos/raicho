import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';

test('send permission is requested synchronously only inside the button gesture', async () => {
  const { installPermissionPrompt } = await import(
    pathToFileURL(resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'mailprobe/src/permission_prompt.js')).href
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
  assert.equal(status.textContent, 'Background sending is allowed for this fictional-mail probe.');
});
