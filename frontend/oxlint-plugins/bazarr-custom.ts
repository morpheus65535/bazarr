interface RuleNode {
  type: string;
  [key: string]: unknown;
}

interface RuleContext {
  report(descriptor: { message: string; node: RuleNode }): void;
  filename: string;
}

const dirName = (path: string): string => path.slice(0, path.lastIndexOf("/"));

const resolveRelative = (fromDir: string, relative: string): string => {
  const stack: string[] = [];
  for (const part of `${fromDir}/${relative}`.split("/")) {
    if (part === "" || part === ".") {
      continue;
    }
    if (part === "..") {
      stack.pop();
    } else {
      stack.push(part);
    }
  }
  return `/${stack.join("/")}`;
};

const resolveModuleScssImport = (
  filename: string,
  source: string,
): string | null => {
  if (source.startsWith("./") || source.startsWith("../")) {
    return resolveRelative(dirName(filename), source);
  }

  if (source.startsWith("@/")) {
    const srcIndex = filename.indexOf("/src/");
    if (srcIndex === -1) {
      return null;
    }
    const srcRoot = filename.slice(0, srcIndex + 4);
    return `${srcRoot}/${source.slice(2)}`;
  }

  return null;
};

const isUnderscored = (name: string): boolean => {
  const trimmed = name.replace(/^_+|_+$/g, "");
  return trimmed.includes("_") && trimmed !== trimmed.toUpperCase();
};

const reportNonCamelCase = (
  context: RuleContext,
  node: RuleNode,
  name: string,
): void => {
  if (!isUnderscored(name)) {
    return;
  }

  context.report({
    message: `Identifier '${name}' is not in camel case.`,
    node,
  });
};

const plugin = {
  meta: {
    name: "bazarr-custom",
  },
  rules: {
    camelcase: {
      create(context: RuleContext) {
        return {
          "VariableDeclarator, FunctionDeclaration, ClassDeclaration"(
            node: RuleNode,
          ) {
            const id = node.id as RuleNode | null;
            if (id?.type === "Identifier") {
              reportNonCamelCase(context, id, id.name as string);
            }
          },
          "FunctionDeclaration, FunctionExpression, ArrowFunctionExpression": (
            node: RuleNode,
          ) => {
            for (const param of node.params as RuleNode[]) {
              if (param.type === "Identifier") {
                reportNonCamelCase(context, param, param.name as string);
              }
            }
          },
          "MethodDefinition, PropertyDefinition"(node: RuleNode) {
            const key = node.key as RuleNode;
            if (!node.computed && key.type === "Identifier") {
              reportNonCamelCase(context, key, key.name as string);
            }
          },
          "ImportDefaultSpecifier, ImportSpecifier, ImportNamespaceSpecifier"(
            node: RuleNode,
          ) {
            const local = node.local as RuleNode;
            reportNonCamelCase(context, local, local.name as string);
          },
          CatchClause(node: RuleNode) {
            const param = node.param as RuleNode | null;
            if (param?.type === "Identifier") {
              reportNonCamelCase(context, param, param.name as string);
            }
          },
        };
      },
    },
    "no-let": {
      create(context: RuleContext) {
        return {
          VariableDeclaration(node: RuleNode) {
            if (node.kind === "let") {
              context.report({ message: "Use const instead of let.", node });
            }
          },
        };
      },
    },
    "no-function-declaration": {
      create(context: RuleContext) {
        return {
          FunctionDeclaration(node: RuleNode) {
            context.report({
              message: "Use const instead of function declaration.",
              node,
            });
          },
        };
      },
    },
    "no-cross-module-scss-import": {
      create(context: RuleContext) {
        return {
          ImportDeclaration(node: RuleNode) {
            const source = node.source as RuleNode;
            const value = source.value as string;

            if (!/\.module\.(scss|css)$/.test(value)) {
              return;
            }

            const resolved = resolveModuleScssImport(context.filename, value);
            if (resolved === null) {
              return;
            }

            const srcIndex = context.filename.indexOf("/src/");
            const srcRoot =
              srcIndex === -1 ? null : context.filename.slice(0, srcIndex + 4);

            if (srcRoot !== null && resolved.startsWith(`${srcRoot}/assets/`)) {
              return;
            }

            if (dirName(resolved) === dirName(context.filename)) {
              return;
            }

            context.report({
              message:
                "Don't import another component's own .module.scss/.css across directories. Co-locate the class with its component, or share tokens via '@/assets'.",
              node,
            });
          },
        };
      },
    },
  },
};

export default plugin;
