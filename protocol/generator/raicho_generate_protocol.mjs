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
const outputDirectory = process.argv[2];
if (
  !outputDirectory ||
  !isAbsolute(outputDirectory) ||
  process.argv.length !== 3
) {
  throw new Error('Supply one absolute protocol output directory.');
}

const schema = JSON.parse(
  await readFile(
    resolve(repositoryRoot, 'protocol/schema/connector.schema.json'),
    'utf8',
  ),
);
const limits = JSON.parse(
  await readFile(resolve(repositoryRoot, 'protocol/limits.json'), 'utf8'),
);

function checkLocalReferences(value) {
  if (!value || typeof value !== 'object') return;
  for (const [key, child] of Object.entries(value)) {
    if (
      key === '$ref' &&
      (typeof child !== 'string' || !child.startsWith('#/'))
    ) {
      throw new Error(
        'Protocol generation accepts only local schema references.',
      );
    }
    checkLocalReferences(child);
  }
}
checkLocalReferences(schema);

const validator = new Ajv({
  strict: true,
  allErrors: false,
  ownProperties: true,
  code: { source: true, esm: true },
});
const validate = validator.compile(schema);
const generated = await build({
  absWorkingDir: '/opt/quality',
  stdin: {
    contents: standaloneCode(validator, validate),
    resolveDir: '/opt/quality',
    sourcefile: 'validator_generated.js',
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
  'validator_generated.js',
  validatorSource,
  typescript.ScriptTarget.ES2022,
  true,
  typescript.ScriptKind.JS,
);
function checkStandalone(node) {
  if (
    typescript.isImportDeclaration(node) ||
    (typescript.isExportDeclaration(node) && node.moduleSpecifier) ||
    ((typescript.isCallExpression(node) || typescript.isNewExpression(node)) &&
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

const files = {
  'contract_generated.ts': await compile(schema, 'ConnectorMessage', {
    bannerComment: '// Generated from protocol/schema/connector.schema.json.',
    unknownAny: true,
    unreachableDefinitions: true,
    style: { singleQuote: true },
  }),
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
await mkdir(outputDirectory, { recursive: true });
for (const [filename, content] of Object.entries(files)) {
  await writeFile(
    resolve(outputDirectory, filename),
    await format(content, {
      parser: filename.endsWith('.js') ? 'babel' : 'typescript',
      singleQuote: true,
    }),
  );
}
