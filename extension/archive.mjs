import { Buffer } from 'node:buffer';
import { mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { crc32 } from 'node:zlib';

// The DOS date for 1980-01-01, the earliest timestamp a ZIP entry can carry.
const FIXED_DATE = 0x21;
const REGULAR_FILE_MODE = 0o100644;

export function archiveEntries(directory) {
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
  const buffer = Buffer.alloc(fields.reduce((size, [bytes]) => size + bytes, 0));
  let offset = 0;
  for (const [bytes, value] of fields) {
    if (bytes === 2) buffer.writeUInt16LE(value, offset);
    else buffer.writeUInt32LE(value, offset);
    offset += bytes;
  }
  return buffer;
}

// Stored entries with fixed metadata keep the archive byte-for-byte reproducible.
export function writeArchive(output, entries) {
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
    const record = Buffer.concat([header([[4, 0x04034b50], [2, 20], ...common]), name, contents]);
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
