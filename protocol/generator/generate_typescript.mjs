import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, isAbsolute, resolve } from 'node:path';
import process from 'node:process';
import { fileURLToPath } from 'node:url';

const require = createRequire('/opt/quality/package.json');
const Ajv = require('ajv');
const standaloneCode = require('ajv/dist/standalone').default;
const { compile } = require('json-schema-to-typescript');
const { build } = require('esbuild');
const { format } = require('prettier');
const typescript = require('typescript');
const repositoryRoot = resolve(
  dirname(fileURLToPath(import.meta.url)),
  '../..',
);
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

const schema = JSON.parse(
  await readFile(
    resolve(repositoryRoot, 'protocol/schema/connector.schema.json'),
    'utf8',
  ),
);
const statusSchema = JSON.parse(
  await readFile(
    resolve(repositoryRoot, 'protocol/schema/status.schema.json'),
    'utf8',
  ),
);
const limits = JSON.parse(
  await readFile(resolve(repositoryRoot, 'protocol/limits.json'), 'utf8'),
);
const diagnostics = JSON.parse(
  await readFile(resolve(repositoryRoot, 'protocol/diagnostics.json'), 'utf8'),
);

async function standaloneValidator(source, filename) {
  const validator = new Ajv({
    strict: true,
    allErrors: false,
    ownProperties: true,
    code: { source: true, esm: true },
  });
  const validate = validator.compile(source);
  const generated = await build({
    absWorkingDir: '/opt/quality',
    stdin: {
      contents: standaloneCode(validator, validate),
      resolveDir: '/opt/quality',
      sourcefile: filename,
    },
    bundle: true,
    write: false,
    platform: 'browser',
    format: 'esm',
    target: 'es2022',
    legalComments: 'none',
  });
  const validatorSource = generated.outputFiles[0]?.text;
  if (!validatorSource) {
    throw new Error(
      'The generated validator must be self-contained and CSP safe.',
    );
  }
  const syntaxTree = typescript.createSourceFile(
    filename,
    validatorSource,
    typescript.ScriptTarget.ES2022,
    true,
    typescript.ScriptKind.JS,
  );
  function checkStandalone(node) {
    if (
      typescript.isImportDeclaration(node) ||
      (typescript.isExportDeclaration(node) && node.moduleSpecifier) ||
      ((typescript.isCallExpression(node) ||
        typescript.isNewExpression(node)) &&
        (node.expression.kind === typescript.SyntaxKind.ImportKeyword ||
          /^(?:require|eval|Function|globalThis\.(?:eval|Function))$/u.test(
            node.expression.getText(syntaxTree),
          )))
    ) {
      throw new Error(
        'The generated validator must be self-contained and CSP safe.',
      );
    }
    typescript.forEachChild(node, checkStandalone);
  }
  checkStandalone(syntaxTree);
  return validatorSource;
}
const validatorSource = await standaloneValidator(
  schema,
  'validator_generated.js',
);
const statusValidatorSource = await standaloneValidator(
  statusSchema,
  'status_validator_generated.js',
);

const files = {
  'contract_generated.ts': await compile(schema, 'ConnectorMessage', {
    bannerComment: '// Generated from protocol/schema/connector.schema.json.',
    unknownAny: true,
    unreachableDefinitions: true,
    style: { singleQuote: true },
  }),
  'diagnostics_generated.ts':
    '// Generated from protocol/diagnostics.json.\n' +
    `export const CONTRACT_ERRORS = ${JSON.stringify(diagnostics.contract_errors)} as const;\n` +
    'export type ContractErrorCode = (typeof CONTRACT_ERRORS)[number];\n',
  'limits_generated.ts':
    '// Generated from protocol/limits.json.\n' +
    `export const LIMITS = ${JSON.stringify(limits)} as const;\n`,
  'validator_generated.js':
    '// Generated from protocol/schema/connector.schema.json.\n' +
    validatorSource,
  'validator_generated.d.ts':
    '// Generated from protocol/schema/connector.schema.json.\n' +
    "import type { ConnectorMessage } from './contract_generated.js';\n" +
    'export default function validate(value: unknown): value is ConnectorMessage;\n',
};
const webFiles = {
  'status_generated.ts': await compile(statusSchema, 'ApplicationStatus', {
    bannerComment: '// Generated from protocol/schema/status.schema.json.',
    unknownAny: true,
    unreachableDefinitions: true,
    style: { singleQuote: true },
  }),
  'status_validator_generated.js':
    '// Generated from protocol/schema/status.schema.json.\n' +
    statusValidatorSource,
  'status_validator_generated.d.ts':
    '// Generated from protocol/schema/status.schema.json.\n' +
    "import type { ApplicationStatus } from './status_generated.js';\n" +
    'export default function validate(value: unknown): value is ApplicationStatus;\n',
};
for (const [directory, outputs] of [
  [outputDirectory, files],
  [webDirectory, webFiles],
]) {
  await mkdir(directory, { recursive: true });
  for (const [filename, content] of Object.entries(outputs)) {
    await writeFile(
      resolve(directory, filename),
      await format(content, {
        parser: filename.endsWith('.js') ? 'babel' : 'typescript',
        singleQuote: true,
      }),
    );
  }
}
