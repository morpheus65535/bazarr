// eslint-disable-next-line no-restricted-imports
import { dependencies } from "../package.json" with { type: "json" };

const groups: Record<string, string[]> = {
  vendors: ["react", "react-router", "react-dom"],
  ui: [
    "@mantine/core",
    "@mantine/hooks",
    "@mantine/form",
    "@mantine/modals",
    "@mantine/notifications",
    "@mantine/dropzone",
  ],
  query: [
    "@tanstack/react-query",
    "@tanstack/react-query-devtools",
    "@tanstack/react-table",
  ],
  charts: [
    "recharts",
    "d3-array",
    "d3-interpolate",
    "d3-scale",
    "d3-shape",
    "d3-time",
  ],
  utils: ["axios", "socket.io-client", "lodash", "clsx"],
};

function buildLookup(): Record<string, string> {
  const lookup: Record<string, string> = {};
  const excludeList: string[] = [];

  for (const [group, packages] of Object.entries(groups)) {
    for (const pkg of packages) {
      lookup[pkg] = group;
      excludeList.push(pkg);
    }
  }

  for (const key in dependencies) {
    if (!excludeList.includes(key)) {
      lookup[key] = key;
    }
  }

  return lookup;
}

const lookup = buildLookup();

export default function manualChunks(id: string): string | undefined {
  for (const [pkg, group] of Object.entries(lookup)) {
    if (id.includes(`/node_modules/${pkg}/`)) {
      return group;
    }
  }
}
