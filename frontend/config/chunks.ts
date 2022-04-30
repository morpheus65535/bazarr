import { dependencies } from "../package.json";

const vendors = [
  "react",
  "react-redux",
  "react-router-dom",
  "react-dom",
  "react-query",
  "axios",
  "socket.io-client",
];

function renderChunks() {
  const chunks: Record<string, string[]> = {};

  for (const key in dependencies) {
    if (!vendors.includes(key)) {
      chunks[key] = [key];
    }
  }

  return chunks;
}

const chunks = {
  vendors,
  ...renderChunks(),
};

export default chunks;
