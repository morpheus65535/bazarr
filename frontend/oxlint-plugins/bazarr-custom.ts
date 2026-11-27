interface RuleNode {
  type: string;
  [key: string]: unknown;
}

interface RuleContext {
  report(descriptor: { message: string; node: RuleNode }): void;
  filename: string;
}

interface RuleScope {
  set: Map<string, { defs: { node: RuleNode }[] }>;
  upper: RuleScope | null;
}

interface ScopedRuleContext extends RuleContext {
  sourceCode: { getScope(node: RuleNode): RuleScope };
}

const findBinding = (context: ScopedRuleContext, identifier: RuleNode) => {
  for (
    let scope: RuleScope | null = context.sourceCode.getScope(identifier);
    scope !== null;
    scope = scope.upper
  ) {
    const binding = scope.set.get(identifier.name as string);
    if (binding) {
      return binding.defs[0]?.node;
    }
  }
};

const testingLibraryImports = new Set([
  "@/tests",
  "@testing-library/dom",
  "@testing-library/react",
]);

const getTestingLibraryImport = (
  context: ScopedRuleContext,
  identifier: RuleNode,
): string | undefined => {
  if (identifier.type !== "Identifier") {
    return;
  }

  const binding = findBinding(context, identifier);
  const declaration = binding?.parent as RuleNode | undefined;
  const source = (declaration?.source as RuleNode | undefined)?.value;

  if (source === "@testing-library/user-event") {
    const imported = (binding?.imported as RuleNode | undefined)?.name;
    if (
      binding?.type === "ImportDefaultSpecifier" ||
      imported === "userEvent"
    ) {
      return "userEvent";
    }
  }

  if (
    typeof source === "string" &&
    testingLibraryImports.has(source) &&
    binding?.type === "ImportSpecifier"
  ) {
    return (binding.imported as RuleNode).name as string;
  }
};

const isUserEventSession = (
  context: ScopedRuleContext,
  identifier: RuleNode,
): boolean => {
  if (identifier.type !== "Identifier") {
    return false;
  }

  const binding = findBinding(context, identifier);
  const initializer = binding?.init as RuleNode | undefined;
  const callee = initializer?.callee as RuleNode | undefined;
  return (
    binding?.type === "VariableDeclarator" &&
    initializer?.type === "CallExpression" &&
    callee?.type === "MemberExpression" &&
    !callee.computed &&
    (callee.property as RuleNode).name === "setup" &&
    getTestingLibraryImport(context, callee.object as RuleNode) === "userEvent"
  );
};

const testingLibraryActions = new Set([
  "act",
  "customRender",
  "fireEvent",
  "rawRender",
  "render",
  "renderHook",
]);

const isTestingLibraryAction = (
  context: ScopedRuleContext,
  callee: RuleNode,
): boolean => {
  if (callee.type === "MemberExpression") {
    const receiver = callee.object as RuleNode;
    const imported = getTestingLibraryImport(context, receiver);
    return (
      imported === "fireEvent" ||
      imported === "userEvent" ||
      isUserEventSession(context, receiver)
    );
  }

  const imported = getTestingLibraryImport(context, callee);
  return imported !== undefined && testingLibraryActions.has(imported);
};

const isInsideWaitFor = (context: ScopedRuleContext, node: RuleNode) => {
  for (
    let ancestor = node.parent as RuleNode | undefined;
    ancestor;
    ancestor = ancestor.parent as RuleNode | undefined
  ) {
    if (
      ancestor.type === "ArrowFunctionExpression" ||
      ancestor.type === "FunctionExpression" ||
      ancestor.type === "FunctionDeclaration"
    ) {
      const call = ancestor.parent as RuleNode | undefined;
      return (
        call?.type === "CallExpression" &&
        (call.arguments as RuleNode[])[0] === ancestor &&
        getTestingLibraryImport(context, call.callee as RuleNode) === "waitFor"
      );
    }
  }

  return false;
};

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
    "no-wait-for-side-effects": {
      create(context: ScopedRuleContext) {
        return {
          CallExpression(node: RuleNode) {
            if (
              isTestingLibraryAction(context, node.callee as RuleNode) &&
              isInsideWaitFor(context, node)
            ) {
              context.report({
                message:
                  "Run Testing Library actions outside waitFor; its callback can run more than once.",
                node,
              });
            }
          },
        };
      },
    },
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
