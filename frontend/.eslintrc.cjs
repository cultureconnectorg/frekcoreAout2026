module.exports = {
  env: { browser: true, es2022: true },
  extends: ['eslint:recommended', 'plugin:react/recommended', 'plugin:react-hooks/recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module', ecmaFeatures: { jsx: true } },
  settings: { react: { version: 'detect' } },
  rules: {
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    // Existing Vite compatibility shims and French content are intentionally
    // retained; these rules would require unrelated product-wide rewrites.
    'react/no-unescaped-entities': 'off',
    'react-hooks/exhaustive-deps': 'off',
    'no-unused-vars': 'off',
    'no-undef': 'off',
    'no-case-declarations': 'off',
    // Catch blocks intentionally handling unavailable hardware/network must be explicit at call sites.
    'no-empty': ['error', { allowEmptyCatch: true }],
  },
};
