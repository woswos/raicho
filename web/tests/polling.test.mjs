import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { setImmediate } from 'node:timers/promises';
import { pathToFileURL } from 'node:url';
import { mockBrowser } from './polling_browser.js';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { createStatusPoller } = await import(
  pathToFileURL(resolve(outputDirectory, 'status_poller.js')).href
);

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
    json: () =>
      Promise.resolve({
        status: 'ready',
        database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
        backend: { status: 'unconfigured', kind: 'thunderbird' },
        version: '0.1.0',
        commit: 'unknown',
      }),
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
