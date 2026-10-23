import { execFileSync } from 'node:child_process';
import {
  cpSync,
  existsSync,
  mkdirSync,
  readdirSync,
  writeFileSync,
} from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const repositoryRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../..',
);
const output = process.argv[2];
if (!output || !path.isAbsolute(output)) {
  throw new Error('Supply an absolute, empty output directory.');
}
if (existsSync(output) && readdirSync(output).length !== 0) {
  throw new Error('The web output directory must be empty.');
}
mkdirSync(output, { recursive: true });
execFileSync(
  'tsc',
  [
    '--project',
    path.join(repositoryRoot, 'web/tsconfig.json'),
    '--outDir',
    output,
  ],
  {
    stdio: 'inherit',
  },
);
cpSync(path.join(repositoryRoot, 'web/public'), output, { recursive: true });
for (const asset of [
  'logos/horizontal.svg',
  'logos/horizontal-dark.svg',
  'fonts/fonts.css',
  'fonts/Geologica-Variable.woff2',
  'fonts/OFL.txt',
  'tokens.css',
  'icons/favicon.svg',
]) {
  const destination = path.join(output, 'assets/brand', asset);
  mkdirSync(path.dirname(destination), { recursive: true });
  cpSync(path.join(repositoryRoot, 'assets/brand', asset), destination);
}
writeFileSync(path.join(output, 'package.json'), '{"type":"module"}\n');
