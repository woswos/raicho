import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const outputDirectory = process.env.RAICHO_WEB_BUILD_DIR ?? 'web/dist';
const { readStatus } = await import(pathToFileURL(resolve(outputDirectory, 'status.js')).href);
const documents = JSON.parse(
  await readFile(new URL('../../protocol/fixtures/status/documents.json', import.meta.url), 'utf8'),
);

for (const fixture of documents) {
  test(`shared status fixture: ${fixture.name}`, () => {
    assert.equal(readStatus(fixture.document) !== undefined, fixture.valid);
  });
}
