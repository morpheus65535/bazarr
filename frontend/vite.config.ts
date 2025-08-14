/* eslint-disable camelcase */

/// <reference types="vitest" />
/// <reference types="vite/client" />
/// <reference types="node" />

import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig, loadEnv } from "vite";
import checker from "vite-plugin-checker";
import { VitePWA } from "vite-plugin-pwa";
import chunks from "./config/chunks";
import overrideEnv from "./config/configReader";

export default defineConfig(({ mode, command }) => {
  const env = loadEnv(mode, process.cwd());

  if (command === "serve") {
    overrideEnv(env);
  }

  const target = env.VITE_PROXY_URL;
  const ws = env.VITE_ALLOW_WEBSOCKET === "true";
  const secure = env.VITE_PROXY_SECURE === "true";

  const imagesFolder = mode === "development" ? "public/images" : "images";

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
      VitePWA({
        workbox: {
          globIgnores: ["index.html"],
        },
        registerType: "autoUpdate",
        includeAssets: [
          `${imagesFolder}/favicon.ico`,
          `${imagesFolder}/apple-touch-icon-180x180.png`,
        ],
        manifest: {
          name: "Bazarr",
          short_name: "Bazarr",
          description:
            "Bazarr is a companion application to Sonarr and Radarr. It manages and downloads subtitles based on your requirements.",
          theme_color: "#be4bdb",
          icons: [
            {
              src: `${imagesFolder}/pwa-64x64.png`,
              sizes: "64x64",
              type: "image/png",
            },
            {
              src: `${imagesFolder}/pwa-192x192.png`,
              sizes: "192x192",
              type: "image/png",
            },
            {
              src: `${imagesFolder}/pwa-512x512.png`,
              sizes: "512x512",
              type: "image/png",
            },
          ],
          screenshots: [
            {
              src: `/${imagesFolder}/pwa-wide-series-list.jpeg`,
              sizes: "1447x1060",
              label: "Series List",
              form_factor: "wide",
              type: "image/jpeg",
            },
            {
              src: `/${imagesFolder}/pwa-wide-series-overview.jpeg`,
              sizes: "1447x1060",
              label: "Series Overview",
              form_factor: "wide",
              type: "image/jpeg",
            },
            {
              src: `/${imagesFolder}/pwa-narrow-series-list.jpeg`,
              sizes: "491x973",
              label: "Series List",
              form_factor: "narrow",
              type: "image/jpeg",
            },
            {
              src: `/${imagesFolder}/pwa-narrow-series-overview.jpeg`,
              sizes: "491x973",
              label: "Series Overview",
              form_factor: "narrow",
              type: "image/jpeg",
            },
          ],
        },
        devOptions: {
          enabled: mode === "development",
        },
      }),
    ],
    css: {
      preprocessorOptions: {
        scss: {
          api: "modern-compiler",
          additionalData: `
            @use "${path.join(process.cwd(), "src/assets/_mantine").replace(/\\/g, "/")}" as mantine;
            @use "${path.join(process.cwd(), "src/assets/_bazarr").replace(/\\/g, "/")}" as bazarr;
          `,
        },
      },
    },
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
      chunkSizeWarningLimit: 600,
      rollupOptions: {
        output: {
          manualChunks: chunks,
        },
      },
    },
    test: {
      globals: true,
      environment: "jsdom",
      setupFiles: "./src/tests/setup.tsx",
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
