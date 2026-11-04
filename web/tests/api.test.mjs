import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { apiPath, apiRequest, REQUEST_TIMEOUT_MS } = await import(
  pathToFileURL(resolve(outputDirectory, 'api.js')).href
);

function browser(context, respond) {
  const timers = new Map();
  const requests = [];
  const original = { window: globalThis.window, fetch: globalThis.fetch };
  globalThis.window = {
    setTimeout(callback, delay) {
      timers.set(timers.size + 1, { callback, delay });
      return timers.size;
    },
    clearTimeout: (timer) => timers.delete(timer),
  };
  globalThis.fetch = (url, options) => {
    requests.push({ url, options });
    return respond(options);
  };
  context.after(() => {
    globalThis.window = original.window;
    globalThis.fetch = original.fetch;
  });
  return { requests, timers };
}

function response(status, body) {
  return Promise.resolve({
    status,
    ok: status >= 200 && status < 300,
    json: () => (typeof body === 'string' ? Promise.reject(new SyntaxError(body)) : Promise.resolve(body)),
  });
}

test('a mutation sends JSON from the same origin and returns the validated document', async (context) => {
  const { requests, timers } = browser(context, () => response(200, { authenticated: true }));
  const result = await apiRequest('/api/session', { method: 'POST', body: { password: 'fictional password' } });
  assert.deepEqual(result, { ok: true, document: { authenticated: true } });
  assert.equal(requests[0].options.method, 'POST');
  assert.equal(requests[0].options.credentials, 'same-origin');
  assert.equal(requests[0].options.cache, 'no-store');
  assert.equal(requests[0].options.headers['Content-Type'], 'application/json');
  assert.equal(requests[0].options.body, '{"password":"fictional password"}');
  assert.equal(timers.size, 0);
});

test('error documents, no content, and unexpected responses are distinguished', async (context) => {
  const responses = [
    response(409, { error: 'stale_cursor' }),
    response(204, ''),
    response(200, { accounts: 'not a list' }),
    response(500, 'not json'),
    response(500, { messages: [] }),
  ];
  browser(context, () => responses.shift());
  assert.deepEqual(await apiRequest('/api/mail/cursors/x'), {
    ok: false,
    failure: { kind: 'api', code: 'stale_cursor' },
  });
  assert.deepEqual(await apiRequest('/api/session', { method: 'DELETE' }), { ok: true, document: null });
  for (let attempt = 0; attempt < 3; attempt += 1) {
    assert.deepEqual(await apiRequest('/api/mail/accounts'), { ok: false, failure: { kind: 'invalid' } });
  }
});

test('network failures and timeouts are reported without details', async (context) => {
  let pending;
  const { timers } = browser(
    context,
    (options) =>
      new Promise((_, reject) => {
        pending = reject;
        options.signal.addEventListener('abort', () => reject(new Error('aborted')));
      }),
  );
  const timed = apiRequest('/api/mail/accounts');
  const [timer] = timers.values();
  assert.equal(timer.delay, REQUEST_TIMEOUT_MS);
  timer.callback();
  assert.deepEqual(await timed, { ok: false, failure: { kind: 'timeout' } });
  const failed = apiRequest('/api/mail/accounts');
  pending(new TypeError('Private network detail'));
  assert.deepEqual(await failed, { ok: false, failure: { kind: 'network' } });
});

test('a route encodes only its handle', () => {
  assert.equal(apiPath('/api/mail/accounts', 'gen.a/b?c', '/mailboxes'), '/api/mail/accounts/gen.a%2Fb%3Fc/mailboxes');
  assert.equal(apiPath('/api/mail/cursors', 'f'.repeat(32)), `/api/mail/cursors/${'f'.repeat(32)}`);
});
