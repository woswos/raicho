import javascript from '@eslint/js';
import { defineConfig } from 'eslint/config';
import prettierConfig from 'eslint-config-prettier/flat';
import globals from 'globals';
import typescriptEslint from 'typescript-eslint';

export default defineConfig(
  {
    ignores: [
      '**/.git/**',
      '**/node_modules/**',
      '**/target/**',
      '**/dist/**',
      'assets/brand/references/**',
    ],
  },
  {
    files: ['**/*.{js,mjs,cjs}'],
    extends: [javascript.configs.recommended],
  },
  {
    files: ['extension/src/contract/validator_generated.js'],
    rules: {
      'no-redeclare': 'off',
      'no-unused-vars': 'off',
      'no-unreachable': 'off',
      'no-useless-assignment': 'off',
    },
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
    extends: [
      javascript.configs.recommended,
      typescriptEslint.configs.recommendedTypeChecked,
    ],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: process.cwd(),
      },
    },
  },
  prettierConfig,
);
