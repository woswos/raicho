import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';
import { mockBrowser } from './polling_browser.js';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { createStatusPoller } = await import(pathToFileURL(resolve(outputDirectory, 'status_poller.js')).href);

function statusDocument(changes = {}) {
  return {
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: {
      status: 'unconfigured',
      kind: 'thunderbird',
      generation: null,
      last_error: null,
      heartbeat_count: 0,
    },
    version: '0.1.0',
    commit: 'unknown',
    ...changes,
  };
}

function pollingFixture(context) {
  const browser = mockBrowser();
  const statuses = [];
  const errors = [];
  const poller = createStatusPoller({
    onLoading() {},
    onStatus: (status) => statuses.push(status),
    onError: (error) => errors.push(error),
  });
  context.after(() => {
    poller.stop();
    browser.restore();
  });
  return { browser, poller, statuses, errors };
}

test('keeps one request in flight and schedules only after it finishes', async (context) => {
  const { browser, poller, statuses } = pollingFixture(context);
  const pending = poller.refresh();
  await poller.refresh();
  assert.equal(browser.requests.length, 1);
  assert.equal(browser.requests[0].url, '/api/status');
  assert.equal(browser.requests[0].options.cache, 'no-store');
  browser.requests[0].resolve({
    ok: true,
    json: () => Promise.resolve(statusDocument()),
  });
  await pending;
  assert.equal(statuses.length, 1);
  assert.deepEqual(
    [...browser.timers.values()].map(({ delay }) => delay),
    [15000],
  );
});

test('does not request while hidden and aborts work when hidden again', async (context) => {
  const { browser, poller, errors } = pollingFixture(context);
  browser.setHidden(true);
  await poller.refresh();
  assert.equal(browser.requests.length, 0);
  browser.setHidden(false);
  assert.equal(browser.requests.length, 1);
  browser.setHidden(true);
  await setImmediate();
  assert.equal(browser.requests[0].options.signal.aborted, true);
  assert.equal(browser.timers.size, 0);
  assert.deepEqual(errors, []);
});

test('times out a request and removes scheduled work when stopped', async (context) => {
  const { browser, poller, errors } = pollingFixture(context);
  const pending = poller.refresh();
  browser.fireTimer(8000);
  await pending;
  assert.deepEqual(errors, ['Raicho took too long to respond. Try again.']);
  poller.stop();
  assert.equal(browser.timers.size, 0);
  await poller.refresh();
  assert.equal(browser.requests.length, 1);
});

test('reports malformed responses without displaying their content', async (context) => {
  const { browser, poller, errors, statuses } = pollingFixture(context);
  const pending = poller.refresh();
  browser.requests[0].resolve({
    ok: true,
    json: () => Promise.resolve('private data'),
  });
  await pending;
  assert.deepEqual(errors, ['Raicho returned an unexpected status response.']);
  assert.deepEqual(statuses, []);
});

test('shows the connector state when the database is unavailable', async (context) => {
  const { browser, poller, errors, statuses } = pollingFixture(context);
  const pending = poller.refresh();
  browser.requests[0].resolve({
    ok: false,
    status: 503,
    json: () =>
      Promise.resolve(
        statusDocument({
          status: 'unavailable',
          database: {
            status: 'unavailable',
            engine: 'sqlite',
            version: '3.51.3',
          },
          backend: {
            status: 'unavailable',
            kind: 'thunderbird',
            generation: null,
            last_error: 'storage_unavailable',
            heartbeat_count: 0,
          },
        }),
      ),
  });
  await pending;
  assert.deepEqual(errors, []);
  assert.equal(statuses[0].database.status, 'unavailable');
  assert.equal(statuses[0].backend.last_error, 'storage_unavailable');
});

for (const [status, json] of [
  [503, () => Promise.resolve('private data')],
  [500, () => Promise.resolve(statusDocument())],
  [502, () => Promise.reject(new SyntaxError('Unexpected token'))],
]) {
  test(`reports a failed ${String(status)} response by status code only`, async (context) => {
    const { browser, poller, errors, statuses } = pollingFixture(context);
    const pending = poller.refresh();
    browser.requests[0].resolve({ ok: false, status, json });
    await pending;
    assert.deepEqual(errors, [`Raicho could not provide its status (HTTP ${String(status)}).`]);
    assert.deepEqual(statuses, []);
  });
}
