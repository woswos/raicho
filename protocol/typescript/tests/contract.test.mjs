import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL, URL } from 'node:url';

const { ContractError, decodeFrame } = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_PROTOCOL_BUILD_DIR, 'decode_frame.js'),
  ).href
);
const fixtureDirectory = new URL('../../fixtures/', import.meta.url);
const fixtureFiles = (await readdir(fixtureDirectory)).filter((filename) =>
  filename.endsWith('.json'),
);
assert.ok(fixtureFiles.length > 0, 'Shared protocol fixtures must exist.');

for (const filename of fixtureFiles.sort()) {
  const fixtures = JSON.parse(
    await readFile(new URL(filename, fixtureDirectory), 'utf8'),
  );
  for (const fixture of fixtures) {
    test(`shared connector fixture: ${fixture.name}`, () => {
      const raw =
        (fixture.raw ?? JSON.stringify(fixture.message)) +
        ' '.repeat(fixture.padding ?? 0);
      if (fixture.valid) {
        assert.deepEqual(
          decodeFrame(raw, fixture.phase, fixture.generation),
          JSON.parse(raw),
        );
      } else {
        assert.throws(
          () => decodeFrame(raw, fixture.phase, fixture.generation),
          (error) =>
            error instanceof ContractError && error.code === fixture.error,
        );
      }
    });
  }
}

test('contract errors do not disclose rejected input', () => {
  const secret = 'private-account-content-and-token';
  assert.throws(
    () => decodeFrame(`{"private":"${secret}"}`, 'authentication'),
    (error) =>
      error instanceof ContractError &&
      error.code === 'invalid_message' &&
      !error.message.includes(secret),
  );
});

test('standalone validator has no runtime code generation or dependencies', async () => {
  const source = await readFile(
    resolve(process.env.RAICHO_PROTOCOL_BUILD_DIR, 'validator_generated.js'),
    'utf8',
  );
  assert.doesNotMatch(source, /\bimport\s*(?:\(|["'{*])/u);
  const originalFunction = globalThis.Function;
  const originalEval = globalThis.eval;
  function blocked() {
    throw new Error('Dynamic code generation is forbidden.');
  }
  try {
    globalThis.Function = blocked;
    globalThis.eval = blocked;
    const { default: validate } = await import(
      `data:text/javascript,${encodeURIComponent(source)}`
    );
    assert.equal(validate({}), false);
    assert.equal(validate(null), false);
  } finally {
    globalThis.Function = originalFunction;
    globalThis.eval = originalEval;
  }
});
