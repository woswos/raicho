import assert from 'node:assert/strict';
import { resolve } from 'node:path';
import process from 'node:process';
import { test } from 'node:test';
import { pathToFileURL } from 'node:url';

const { isUnambiguousJson } = await import(
  pathToFileURL(
    resolve(process.env.RAICHO_EXTENSION_BUILD_DIR, 'contract/raw_json.js'),
  ).href
);

test('raw JSON rejects duplicate members including escaped aliases', () => {
  for (const raw of [
    '{"member":1,"member":2}',
    '{"member":1,"mem\\u0062er":2}',
    '[{"member":1,"member":2}]',
    '{"nested":{"member":1,"member":2}}',
    '{"member":1e999,"member":2}',
    '{"member":"\\ud800","member":2}',
    String.raw`{"quote\"":1,"quote\"":2}`,
  ]) {
    JSON.parse(raw);
    assert.equal(isUnambiguousJson(raw, 64), false, raw);
  }
});

test('raw JSON tracks keys per object and ignores punctuation in strings', () => {
  for (const raw of [
    '[{"member":1},{"member":2}]',
    '{"member":{"member":2}}',
    String.raw`{"first":"{\"member\":1,\"member\":2}","second":"[],:"}`,
    String.raw`{"quote\"":1,"slash\\":2}`,
    '{"first":[true,false,null,42,1.2e4,"text"],"second":{}}',
    '"a root string"',
  ]) {
    JSON.parse(raw);
    assert.equal(isUnambiguousJson(raw, 64), true, raw);
  }
});

test('raw JSON bounds container and primitive depth before values disappear', () => {
  assert.equal(isUnambiguousJson('[[]]', 1), true);
  assert.equal(isUnambiguousJson('[[[]]]', 1), false);
  assert.equal(isUnambiguousJson('[[0]]', 1), false);
  assert.equal(isUnambiguousJson('[["text"]]', 1), false);
  assert.equal(isUnambiguousJson('{"member":[[]],"member":0}', 1), false);
});
