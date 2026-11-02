import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, isAbsolute, resolve } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

import { requireQuality, standaloneValidator } from './standalone_validator.mjs';

const { compile } = requireQuality('json-schema-to-typescript');
const { format } = requireQuality('prettier');
const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const formatting = JSON.parse(await readFile(resolve(repositoryRoot, '.prettierrc.json'), 'utf8'));
const [outputDirectory, webDirectory] = process.argv.slice(2);
if (
  !outputDirectory ||
  !webDirectory ||
  !isAbsolute(outputDirectory) ||
  !isAbsolute(webDirectory) ||
  process.argv.length !== 4
) {
  throw new Error('Supply absolute protocol and web output directories.');
}

const limits = JSON.parse(await readFile(resolve(repositoryRoot, 'protocol/limits.json'), 'utf8'));
const diagnostics = JSON.parse(await readFile(resolve(repositoryRoot, 'protocol/diagnostics.json'), 'utf8'));

function banner(source) {
  return `// Generated from protocol/${source}.\n`;
}

async function schemaOutputs(source, typeName, typesFile, validatorFile) {
  const schema = JSON.parse(await readFile(resolve(repositoryRoot, `protocol/${source}`), 'utf8'));
  const header = banner(source);
  return {
    [typesFile]: await compile(schema, typeName, {
      bannerComment: header.trimEnd(),
      unknownAny: true,
      unreachableDefinitions: true,
      style: { singleQuote: true },
    }),
    [validatorFile]: header + (await standaloneValidator(schema, validatorFile)),
    [validatorFile.replace(/\.js$/u, '.d.ts')]:
      header +
      `import type { ${typeName} } from './${typesFile.replace(/\.ts$/u, '.js')}';\n` +
      `export default function validate(value: unknown): value is ${typeName};\n`,
  };
}

const files = {
  ...(await schemaOutputs(
    'schema/connector.schema.json',
    'ConnectorMessage',
    'contract_generated.ts',
    'validator_generated.js',
  )),
  'diagnostics_generated.ts':
    banner('diagnostics.json') +
    `export type ContractErrorCode = ${diagnostics.contract_errors.map((code) => JSON.stringify(code)).join(' | ')};\n`,
  'limits_generated.ts': banner('limits.json') + `export const LIMITS = ${JSON.stringify(limits)} as const;\n`,
};
const webFiles = await schemaOutputs(
  'schema/status.schema.json',
  'ApplicationStatus',
  'status_generated.ts',
  'status_validator_generated.js',
);
for (const [directory, outputs] of [
  [outputDirectory, files],
  [webDirectory, webFiles],
]) {
  await mkdir(directory, { recursive: true });
  for (const [filename, content] of Object.entries(outputs)) {
    await writeFile(
      resolve(directory, filename),
      await format(content, {
        ...formatting,
        parser: filename.endsWith('.js') ? 'babel' : 'typescript',
      }),
    );
  }
}
