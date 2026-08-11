interface RuleNode {
  type: string;
  [key: string]: unknown;
}

interface RuleContext {
  report(descriptor: { message: string; node: RuleNode }): void;
}

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
  },
};

export default plugin;
