import reactRefresh from "@vitejs/plugin-react-refresh";
import path from "path";
import { defineConfig, loadEnv } from "vite";
import { dependencies } from "./package.json";

const groupedDeps = [
  "react",
  "react-redux",
  "react-router-dom",
  "react-dom",
  "react-query",
  "axios",
  "socket.io-client",
];

function renderChunks(deps: Record<string, string>) {
  const chunks: Record<string, string[]> = {};

  for (const key in deps) {
    if (!groupedDeps.includes(key)) {
      chunks[key] = [key];
    }
  }

  return chunks;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const target = env.VITE_PROXY_URL;
  const allowWs = env.VITE_ALLOW_WEBSOCKET === "true";
  const secure = env.VITE_PROXY_SECURE === "true";

  return {
    plugins: [reactRefresh()],
    base: "./",
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    build: {
      manifest: true,
      sourcemap: mode === "development",
      outDir: "./build",
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: groupedDeps,
            ...renderChunks(dependencies),
          },
        },
      },
    },
    server: {
      proxy: {
        "^/(api|images|test|bazarr.log)/.*": {
          target,
          changeOrigin: true,
          secure,
          ws: allowWs,
        },
      },
    },
  };
});
