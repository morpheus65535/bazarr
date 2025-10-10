// eslint-disable-next-line no-restricted-imports
import { dependencies } from "../package.json";

const vendors = ["react", "react-router", "react-dom"];

const ui = [
  "@mantine/core",
  "@mantine/hooks",
  "@mantine/form",
  "@mantine/modals",
  "@mantine/notifications",
  "@mantine/dropzone",
];

const query = [
  "@tanstack/react-query",
  "@tanstack/react-query-devtools",
  "@tanstack/react-table",
];

const charts = [
  "recharts",
  "d3-array",
  "d3-interpolate",
  "d3-scale",
  "d3-shape",
  "d3-time",
];

const utils = ["axios", "socket.io-client", "lodash", "clsx"];

function renderChunks() {
  const chunks: Record<string, string[]> = {};
  const excludeList = [...vendors, ...ui, ...query, ...charts, ...utils];

  for (const key in dependencies) {
    if (!excludeList.includes(key)) {
      chunks[key] = [key];
    }
  }

  return chunks;
}

const chunks = {
  vendors,
  ui,
  query,
  charts,
  utils,
  ...renderChunks(),
};

export default chunks;
