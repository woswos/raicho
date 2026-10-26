import path from 'node:path';
import process from 'node:process';
import { inspect } from 'node:util';

function location(data) {
  if (!data.file) return '';
  const file = path.relative(process.cwd(), data.file);
  return data.line ? ` (${file}:${String(data.line)})` : ` (${file})`;
}

function failureDetail(data) {
  const error = data.details?.error;
  return inspect(error?.cause ?? error, { depth: 4 });
}

export default async function* nodeReporter(source) {
  let passed = 0;
  let skipped = 0;
  let failed = 0;
  const directories = new Set();
  const output = [];
  for await (const { type, data } of source) {
    if (type === 'test:stdout' || type === 'test:stderr') {
      output.push(data.message);
    } else if (data?.details?.type === 'suite') {
      continue;
    } else if (type === 'test:pass') {
      if (data.skip !== undefined || data.todo !== undefined) skipped += 1;
      else passed += 1;
      if (data.file) {
        directories.add(
          path.relative(process.cwd(), path.dirname(data.file)) || '.',
        );
      }
    } else if (
      type === 'test:fail' &&
      data.details?.error?.failureType !== 'subtestsFailed'
    ) {
      failed += 1;
      yield `✖ ${data.name}${location(data)}\n${failureDetail(data)}\n\n`;
    }
  }
  if (failed) {
    yield output.join('');
    yield `Node: ${String(failed)} failed, ${String(passed)} passed\n`;
    return;
  }
  const skippedText = skipped ? `, ${String(skipped)} skipped` : '';
  yield `Node: ${String(passed)} tests passed${skippedText} in ${[...directories].sort().join(', ')}\n`;
}
