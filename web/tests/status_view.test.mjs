import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { createStatusView } = await import(pathToFileURL(resolve(outputDirectory, 'status_view.js')).href);

function viewFixture(context) {
  const originalValues = new Map(
    ['document', 'HTMLButtonElement'].map((name) => [name, Object.getOwnPropertyDescriptor(globalThis, name)]),
  );
  class MockButton {
    disabled = false;
    textContent = '';
    attributes = new Map();

    setAttribute(name, value) {
      this.attributes.set(name, value);
    }

    getAttribute(name) {
      return this.attributes.get(name) ?? null;
    }
  }
  const elements = new Map([['refresh', new MockButton()]]);
  globalThis.HTMLButtonElement = MockButton;
  globalThis.document = {
    getElementById(identifier) {
      if (!elements.has(identifier)) {
        elements.set(identifier, { dataset: {}, textContent: '' });
      }
      return elements.get(identifier);
    },
  };
  context.after(() => {
    for (const [name, descriptor] of originalValues) {
      if (descriptor) Object.defineProperty(globalThis, name, descriptor);
      else delete globalThis[name];
    }
  });
  return createStatusView();
}

test('initial refresh control conveys loading without native disabling', async () => {
  const markup = await readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  const refreshButton = markup.match(/<button\b[^>]*\bid="refresh"[^>]*>/)?.[0];
  assert.ok(refreshButton);
  assert.match(refreshButton, /\saria-disabled="true"/);
  assert.doesNotMatch(refreshButton, /\sdisabled(?:\s|=|>)/);
});

test('loading leaves the refresh control natively enabled', (context) => {
  const view = viewFixture(context);
  view.onLoading();
  assert.equal(view.refreshButton.disabled, false);
  assert.equal(view.refreshButton.getAttribute('aria-disabled'), 'true');
  assert.equal(view.refreshButton.textContent, 'Checking…');
});

test('success makes the refresh control available again', (context) => {
  const view = viewFixture(context);
  view.onLoading();
  view.onStatus({
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: { status: 'unconfigured', kind: 'thunderbird', last_error: null },
    version: '0.1.0',
    commit: 'unknown',
  });
  assert.equal(globalThis.document.getElementById('application-version').textContent, '0.1.0');
  view.onStatus({
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: { status: 'unconfigured', kind: 'thunderbird', last_error: null },
    version: '0.1.0',
    commit: '0123456789abcdef0123456789abcdef01234567',
  });
  assert.equal(
    globalThis.document.getElementById('application-version').textContent,
    '0.1.0 (0123456789abcdef0123456789abcdef01234567)',
  );
  assert.equal(view.refreshButton.disabled, false);
  assert.equal(view.refreshButton.getAttribute('aria-disabled'), 'false');
  assert.equal(view.refreshButton.textContent, 'Refresh status');
});

test('failure makes the refresh control available for retry', (context) => {
  const view = viewFixture(context);
  view.onLoading();
  view.onError('Raicho could not be reached.');
  assert.equal(view.refreshButton.disabled, false);
  assert.equal(view.refreshButton.getAttribute('aria-disabled'), 'false');
  assert.equal(view.refreshButton.textContent, 'Refresh status');
});

test('reports connector transitions independently of application readiness', (context) => {
  const view = viewFixture(context);
  const { document } = globalThis;
  const ready = {
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    version: '0.1.0',
    commit: '0123456789abcdef0123456789abcdef01234567',
  };
  for (const [status, label] of [
    ['connected', 'Connected'],
    ['disconnected', 'Disconnected'],
    ['revoked', 'Access revoked'],
    ['unavailable', 'Unavailable'],
    ['unconfigured', 'Not configured'],
  ]) {
    view.onStatus({
      ...ready,
      backend: { kind: 'thunderbird', status, last_error: null },
    });
    assert.equal(document.getElementById('backend-status').textContent, label);
    assert.equal(document.getElementById('server-status').textContent, 'Ready');
    assert.equal(
      document.getElementById('application-version').textContent,
      '0.1.0 (0123456789abcdef0123456789abcdef01234567)',
    );
    assert.match(document.getElementById('announcement').textContent, /Thunderbird/);
    assert.ok(document.getElementById('announcement').textContent.includes(label));
  }
});

test('connected diagnostics do not claim mailbox availability', (context) => {
  const view = viewFixture(context);
  const { document } = globalThis;
  view.onStatus({
    status: 'ready',
    database: { status: 'ready', engine: 'sqlite', version: '3.51.3' },
    backend: { kind: 'thunderbird', status: 'connected', last_error: null },
    version: '0.1.0',
    commit: 'unknown',
  });
  assert.match(document.getElementById('backend-description').textContent, /Mail is not available/);
  assert.equal(document.getElementById('backend-status').dataset.state, 'ready');
  view.onError('Raicho could not be reached.');
  assert.equal(document.getElementById('backend-status').textContent, 'Not checked');
  assert.notEqual(document.getElementById('backend-status').dataset.state, 'ready');
});

test('a database outage keeps the connector state visible', (context) => {
  const view = viewFixture(context);
  const { document } = globalThis;
  view.onStatus({
    status: 'unavailable',
    database: { status: 'unavailable', engine: 'sqlite', version: '3.51.3' },
    backend: {
      kind: 'thunderbird',
      status: 'unavailable',
      last_error: 'storage_unavailable',
    },
    version: '0.1.0',
    commit: 'unknown',
  });
  assert.equal(document.getElementById('summary').dataset.state, 'error');
  assert.equal(document.getElementById('server-status').textContent, 'Not ready');
  assert.equal(document.getElementById('database-status').textContent, 'Unavailable');
  assert.equal(document.getElementById('backend-status').textContent, 'Unavailable');
  assert.match(document.getElementById('announcement').textContent, /cannot use its database/);
});
