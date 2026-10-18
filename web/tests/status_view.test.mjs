import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { createStatusView } = await import(
  pathToFileURL(resolve(outputDirectory, 'status_view.js')).href
);

function viewFixture(context) {
  const originalValues = new Map(
    ['document', 'HTMLButtonElement'].map((name) => [
      name,
      Object.getOwnPropertyDescriptor(globalThis, name),
    ]),
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
  const markup = await readFile(
    new URL('../public/index.html', import.meta.url),
    'utf8',
  );
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
    backend: { status: 'unconfigured', kind: 'thunderbird' },
    version: '0.1.0',
  });
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
