import js from '@eslint/js'
import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'

/** Clean Architecture: application must not import infrastructure/api directly. */
const layerBoundaryRules = {
  'no-restricted-imports': [
    'error',
    {
      patterns: [
        {
          group: ['@/infrastructure/api', '@/infrastructure/api/*'],
          message:
            'Application layer must use ports via @/application/container (jobGateway / jobFeaturesGateway / graphGateway), not infrastructure/api.',
        },
      ],
    },
  ],
}

export default tseslint.config(
  { ignores: ['dist/**', 'node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-hooks/exhaustive-deps': 'off',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    files: ['src/application/**/*.{ts,tsx}'],
    ignores: ['src/application/container.ts'],
    rules: layerBoundaryRules,
  },
  {
    files: ['src/domain/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: [
                '@/application/*',
                '@/infrastructure/*',
                '@/presentation/*',
              ],
              message: 'Domain layer must stay pure (no application/infrastructure/presentation imports).',
            },
          ],
        },
      ],
    },
  },
)
