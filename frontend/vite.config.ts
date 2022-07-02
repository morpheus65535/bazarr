/// <reference types="vitest" />
/// <reference types="vite/client" />
/// <reference types="node" />

import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig, loadEnv } from "vite";
import checker from "vite-plugin-checker";
import chunks from "./config/chunks";
import overrideEnv from "./config/configReader";

export default defineConfig(async ({ mode, command }) => {
  const env = loadEnv(mode, process.cwd());

  if (command === "serve") {
    await overrideEnv(env);
  }

  const target = env.VITE_PROXY_URL;
  const ws = env.VITE_ALLOW_WEBSOCKET === "true";
  const secure = env.VITE_PROXY_SECURE === "true";

  return {
    plugins: [
      react(),
      checker({
        typescript: true,
        eslint: {
          lintCommand: "eslint --ext .ts,.tsx src",
        },
        enableBuild: false,
      }),
    ],
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
          manualChunks: chunks,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./test/setup.ts",
    },
    server: {
      proxy: {
        "^/(api|images|test|bazarr.log)/.*": {
          target,
          changeOrigin: true,
          secure,
          ws,
        },
      },
      host: true,
      open: "/",
    },
  };
});
