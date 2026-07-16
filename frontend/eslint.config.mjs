import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import testingLibrary from "eslint-plugin-testing-library";
import globals from "globals";

export default tseslint.config(
  {
    ignores: [
      "dist",
      "build",
      "coverage",
      "node_modules",
      "dev-dist",
      ".husky",
      "eslint.config.mjs",
      "vite.config.ts",
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh.default || reactRefresh,
      "simple-import-sort": simpleImportSort,
    },
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "no-console": "error",
      camelcase: ["error", { properties: "never" }],
      "no-restricted-imports": [
        "error",
        {
          patterns: ["..*"],
        },
      ],
      "simple-import-sort/imports": "error",
      "@typescript-eslint/explicit-module-boundary-types": "off",
      "@typescript-eslint/no-empty-function": "error",
      "@typescript-eslint/no-empty-interface": "off",
      "@typescript-eslint/no-unused-vars": "error",
      "@typescript-eslint/no-empty-object-type": "off",
      "@typescript-eslint/no-unused-expressions": "error",
      "no-useless-assignment": "off",
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/refs": "off",
      "react-hooks/static-components": "off",
      "react-hooks/incompatible-library": "off",
      "no-restricted-syntax": [
        "error",
        {
          selector: "VariableDeclaration[kind='let']",
          message: "Use const instead of let.",
        },
      ],
    },
  },
  {
    files: ["**/*.ts", "**/*.tsx"],
    rules: {
      "simple-import-sort/imports": [
        "error",
        {
          groups: [
            [
              "^react",
              "^@mantine/",
              "^(\\w|@\\w)",
              "^\\u0000",
              "^@/\\w",
              "^\\.\\.(?!/?$)",
              "^\\.\\./?$",
              "^\\./(?=.*/)(?!/?$)",
              "^\\.(?!/?$)",
              "^\\./?$",
              "^.+\\.?(css)$",
            ],
          ],
        },
      ],
    },
  },
  {
    files: ["**/__tests__/**/*.[jt]s?(x)", "**/?(*.)+(spec|test).[jt]s?(x)"],
    ...testingLibrary.configs["flat/react"],
  },
);
