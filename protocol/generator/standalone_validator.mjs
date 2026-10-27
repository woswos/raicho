import { createRequire } from 'node:module';

const require = createRequire('/opt/quality/package.json');
const Ajv = require('ajv');
const standaloneCode = require('ajv/dist/standalone').default;
const { build } = require('esbuild');
const typescript = require('typescript');

function checkStandalone(syntaxTree) {
  function visit(node) {
    if (
      typescript.isImportDeclaration(node) ||
      (typescript.isExportDeclaration(node) && node.moduleSpecifier) ||
      ((typescript.isCallExpression(node) || typescript.isNewExpression(node)) &&
        (node.expression.kind === typescript.SyntaxKind.ImportKeyword ||
          /^(?:require|eval|Function|globalThis\.(?:eval|Function))$/u.test(node.expression.getText(syntaxTree))))
    ) {
      throw new Error('The generated validator must be self-contained and CSP safe.');
    }
    typescript.forEachChild(node, visit);
  }
  visit(syntaxTree);
}

export async function standaloneValidator(schema, filename) {
  const validator = new Ajv({
    strict: true,
    allErrors: false,
    messages: false,
    ownProperties: true,
    code: { source: true, esm: true },
  });
  const validate = validator.compile(schema);
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
    throw new Error('The generated validator must be self-contained and CSP safe.');
  }
  checkStandalone(
    typescript.createSourceFile(
      filename,
      validatorSource,
      typescript.ScriptTarget.ES2022,
      true,
      typescript.ScriptKind.JS,
    ),
  );
  return validatorSource;
}
