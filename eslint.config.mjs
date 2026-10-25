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
      'protocol/typescript/src/validator_generated.js',
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
