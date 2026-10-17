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

const output = process.argv[2];
if (!output || !path.isAbsolute(output)) {
  throw new Error('Supply an absolute, empty output directory.');
}
if (existsSync(output) && readdirSync(output).length !== 0) {
  throw new Error('The web output directory must be empty.');
}
mkdirSync(output, { recursive: true });
execFileSync('tsc', ['--project', 'web/tsconfig.json', '--outDir', output], {
  stdio: 'inherit',
});
cpSync('web/public', output, { recursive: true });
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
  cpSync(path.join('assets/brand', asset), destination);
}
writeFileSync(path.join(output, 'package.json'), '{"type":"module"}\n');
