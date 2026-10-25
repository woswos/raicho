import { Buffer } from 'node:buffer';
import { execFileSync } from 'node:child_process';
import {
  cpSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readdirSync,
  readFileSync,
  rmSync,
  statSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';
import { parseArgs } from 'node:util';
import { crc32 } from 'node:zlib';

const EXTENSION_ROOT = path.dirname(fileURLToPath(import.meta.url));
const VERSION_PATTERN =
  /^(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})\.(0|[1-9][0-9]{0,4})$/u;
// The DOS date for 1980-01-01, the earliest timestamp a ZIP entry can carry.
const FIXED_DATE = 0x21;
const REGULAR_FILE_MODE = 0o100644;

function within(child, parent) {
  const relative = path.relative(parent, child);
  return !relative.startsWith('..') && !path.isAbsolute(relative);
}

function prepareDirectory(directory) {
  if (!path.isAbsolute(directory)) {
    throw new Error('The extension output directory must be absolute.');
  }
  if (
    existsSync(directory) &&
    (!statSync(directory).isDirectory() || readdirSync(directory).length !== 0)
  ) {
    throw new Error('The extension output directory must be empty.');
  }
  mkdirSync(directory, { recursive: true });
}

function extensionManifest(version, sourceRoot) {
  const manifest = JSON.parse(
    readFileSync(path.join(sourceRoot, 'manifest.json'), 'utf8'),
  );
  if (!manifest || typeof manifest !== 'object' || Array.isArray(manifest)) {
    throw new Error('The extension manifest must be an object.');
  }
  const selected = version ?? manifest.version;
  if (
    typeof selected !== 'string' ||
    !VERSION_PATTERN.test(selected) ||
    selected.split('.').some((component) => Number(component) > 65535)
  ) {
    throw new Error(
      'The extension version must contain three components from 0 to 65535 without leading zeros.',
    );
  }
  manifest.version = selected;
  return manifest;
}

function compileExtension(directory, manifest, sourceRoot) {
  execFileSync(
    'tsc',
    [
      '--project',
      path.join(sourceRoot, 'tsconfig.json'),
      '--outDir',
      directory,
    ],
    { stdio: 'inherit' },
  );
  writeFileSync(
    path.join(directory, 'manifest.json'),
    `${JSON.stringify(manifest, null, 2)}\n`,
  );
  cpSync(
    path.join(sourceRoot, 'background.html'),
    path.join(directory, 'background.html'),
  );
  const optionsPage = manifest.options_ui?.page;
  if (optionsPage !== undefined) {
    if (
      typeof optionsPage !== 'string' ||
      !/^[a-z_]+\.html$/u.test(optionsPage)
    ) {
      throw new Error('The options page must be a root-level HTML file.');
    }
    cpSync(
      path.join(sourceRoot, optionsPage),
      path.join(directory, optionsPage),
    );
  }
}

function archiveEntries(directory) {
  return readdirSync(directory, { recursive: true })
    .map((name) => name.split(path.sep).join('/'))
    .filter((name) => statSync(path.join(directory, name)).isFile())
    .sort()
    .map((name) => ({
      name: Buffer.from(name, 'utf8'),
      contents: readFileSync(path.join(directory, name)),
    }));
}

function header(fields) {
  const buffer = Buffer.alloc(
    fields.reduce((size, [bytes]) => size + bytes, 0),
  );
  let offset = 0;
  for (const [bytes, value] of fields) {
    if (bytes === 2) buffer.writeUInt16LE(value, offset);
    else buffer.writeUInt32LE(value, offset);
    offset += bytes;
  }
  return buffer;
}

// Stored entries with fixed metadata keep the archive byte-for-byte reproducible.
function writeArchive(output, entries) {
  if (entries.length > 0xffff) throw new Error('The XPI has too many entries.');
  const local = [];
  const central = [];
  let offset = 0;
  for (const { name, contents } of entries) {
    const checksum = crc32(contents);
    const common = [
      [2, 0],
      [2, 0],
      [2, 0],
      [2, FIXED_DATE],
      [4, checksum],
      [4, contents.length],
      [4, contents.length],
      [2, name.length],
      [2, 0],
    ];
    const record = Buffer.concat([
      header([[4, 0x04034b50], [2, 20], ...common]),
      name,
      contents,
    ]);
    central.push(
      Buffer.concat([
        header([
          [4, 0x02014b50],
          [2, 0x0314],
          [2, 20],
          ...common,
          [2, 0],
          [2, 0],
          [2, 0],
          [4, REGULAR_FILE_MODE * 0x10000],
          [4, offset],
        ]),
        name,
      ]),
    );
    local.push(record);
    offset += record.length;
    if (offset > 0xffffffff) throw new Error('The XPI is too large.');
  }
  const directory = Buffer.concat(central);
  const end = header([
    [4, 0x06054b50],
    [2, 0],
    [2, 0],
    [2, entries.length],
    [2, entries.length],
    [4, directory.length],
    [4, offset],
    [2, 0],
  ]);
  mkdirSync(path.dirname(output), { recursive: true });
  writeFileSync(output, Buffer.concat([...local, directory, end]), {
    flag: 'wx',
  });
}

function build({ output, version, directory, outputDirectory, sourceRoot }) {
  const manifest = extensionManifest(version, sourceRoot);
  if ((output === undefined) === (outputDirectory === undefined)) {
    throw new Error('Choose exactly one extension output mode.');
  }
  if (outputDirectory !== undefined) {
    if (
      directory !== undefined &&
      (within(directory, outputDirectory) || within(outputDirectory, directory))
    ) {
      throw new Error(
        'Artifact and compiled output directories must be separate.',
      );
    }
    prepareDirectory(outputDirectory);
    output = path.join(outputDirectory, `raicho-${manifest.version}.xpi`);
  }
  if (
    !path.isAbsolute(output) ||
    path.extname(output) !== '.xpi' ||
    existsSync(output)
  ) {
    throw new Error('Supply an absolute, unused .xpi output path.');
  }
  if (directory !== undefined) {
    prepareDirectory(directory);
    if (within(output, directory)) {
      throw new Error('The XPI must be outside the compiled output directory.');
    }
  }
  const compiled = mkdtempSync(path.join(tmpdir(), 'raicho-extension-'));
  try {
    compileExtension(compiled, manifest, sourceRoot);
    writeArchive(output, archiveEntries(compiled));
    if (outputDirectory !== undefined) {
      cpSync(
        path.join(compiled, 'manifest.json'),
        path.join(outputDirectory, 'manifest.json'),
      );
    }
    if (directory !== undefined) {
      cpSync(compiled, directory, { recursive: true });
      writeFileSync(
        path.join(directory, 'package.json'),
        '{"type":"module"}\n',
      );
    }
  } finally {
    rmSync(compiled, { recursive: true, force: true });
  }
}

try {
  const { values } = parseArgs({
    options: {
      output: { type: 'string' },
      'output-directory': { type: 'string' },
      version: { type: 'string' },
      directory: { type: 'string' },
      'source-root': { type: 'string', default: EXTENSION_ROOT },
    },
  });
  build({
    output: values.output,
    version: values.version,
    directory: values.directory,
    outputDirectory: values['output-directory'],
    sourceRoot: path.resolve(values['source-root']),
  });
} catch (error) {
  process.stderr.write(
    `FAIL: Could not build the extension: ${error instanceof Error ? error.message : String(error)}\n`,
  );
  process.exitCode = 1;
}
