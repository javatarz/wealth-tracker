import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import { defineConfig, globalIgnores } from "eslint/config";
import globals from "globals";
import tseslint from "typescript-eslint";

export default defineConfig([
  globalIgnores(["dist", "src/api/schema.d.ts"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      js.configs.recommended,
      tseslint.configs.strictTypeChecked,
      tseslint.configs.stylisticTypeChecked,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
      prettier,
    ],
    languageOptions: {
      globals: globals.browser,
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    // Design rules (ADR 0028, docs/agents/code-style.md).
    rules: {
      complexity: ["error", 4],
      "max-depth": ["error", 1],
      "max-params": ["error", 3],
      "max-statements": ["error", 10],
      "max-nested-callbacks": ["error", 3],
      "max-lines-per-function": [
        "error",
        { max: 40, skipBlankLines: true, skipComments: true },
      ],
      "max-lines": [
        "error",
        { max: 150, skipBlankLines: true, skipComments: true },
      ],
      "no-else-return": ["error", { allowElseIf: false }],
      "no-nested-ternary": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector: "IfStatement[alternate]",
          message:
            "Don't use else (Object Calisthenics). Return early, or replace the branch with a lookup.",
        },
        {
          selector: "IfStatement + IfStatement",
          message:
            "If ladder (Object Calisthenics). Replace consecutive ifs with a lookup table keyed by the kind, or polymorphism.",
        },
      ],
    },
  },
  {
    files: ["**/*.test.{ts,tsx}"],
    rules: {
      "max-lines-per-function": "off",
      "max-lines": "off",
      "max-statements": "off",
      "max-nested-callbacks": "off",
    },
  },
]);
