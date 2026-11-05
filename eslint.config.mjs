import javascript from '@eslint/js';
import { defineConfig } from 'eslint/config';
import prettierConfig from 'eslint-config-prettier/flat';
import globals from 'globals';
import typescriptEslint from 'typescript-eslint';

const storageNames = '/^(localStorage|sessionStorage|indexedDB|caches|serviceWorker|getDirectory)$/';
const rawHtmlSinks = '/^(innerHTML|outerHTML|insertAdjacentHTML|createContextualFragment)$/';

export default defineConfig(
  {
    ignores: [
      '**/.git/**',
      '**/node_modules/**',
      '**/target/**',
      '**/dist/**',
      'assets/brand/references/**',
      '**/*validator_generated.js',
    ],
  },
  {
    files: ['**/*.{js,mjs,cjs}'],
    extends: [javascript.configs.recommended],
  },
  {
    files: ['assets/brand/showcase/*.js'],
    languageOptions: {
      sourceType: 'script',
      globals: globals.browser,
    },
  },
  {
    files: ['**/*.config.{js,mjs,cjs}'],
    languageOptions: {
      globals: globals.node,
    },
  },
  {
    files: ['**/*.{ts,tsx,mts,cts}'],
    extends: [javascript.configs.recommended, typescriptEslint.configs.recommendedTypeChecked],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: process.cwd(),
      },
    },
  },
  {
    files: ['web/src/**/*.{ts,tsx}'],
    rules: {
      // Mail must not persist in the browser, so the client never uses browser storage.
      'no-restricted-globals': ['error', 'localStorage', 'sessionStorage', 'indexedDB', 'caches'],
      'no-restricted-syntax': [
        'error',
        {
          selector: [
            `MemberExpression[property.name=${storageNames}]`,
            `MemberExpression[computed=true][property.value=${storageNames}]`,
            `ObjectPattern > Property[key.name=${storageNames}]`,
            `ObjectPattern > Property[key.value=${storageNames}]`,
          ].join(', '),
          message: 'Mail must not persist in the browser.',
        },
        // Mail text renders as JSX text, which Preact escapes, so the client has no raw HTML sink.
        {
          selector: [
            "JSXAttribute[name.name='dangerouslySetInnerHTML']",
            "Property[key.name='dangerouslySetInnerHTML']",
            "Property[key.value='dangerouslySetInnerHTML']",
          ].join(', '),
          message: 'Render mail text as JSX text instead of raw HTML.',
        },
        {
          selector: [
            `MemberExpression[property.name=${rawHtmlSinks}]`,
            `MemberExpression[computed=true][property.value=${rawHtmlSinks}]`,
          ].join(', '),
          message: 'Render mail text as JSX text instead of raw HTML.',
        },
        {
          selector: [
            "CallExpression[callee.object.name='document'][callee.property.name=/^(write|writeln)$/]",
            "CallExpression[callee.object.name='document'][callee.property.value=/^(write|writeln)$/]",
          ].join(', '),
          message: 'Render mail text as JSX text instead of raw HTML.',
        },
      ],
    },
  },
  prettierConfig,
);
