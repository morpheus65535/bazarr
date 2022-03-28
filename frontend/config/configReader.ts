/// <reference types="node" />

import { readFile } from "fs/promises";

async function read(path: string, sectionName: string, fieldName: string) {
  const config = await readFile(path, "utf8");

  const targetSection = config
    .split("\n\n")
    .filter((section) => section.includes(`[${sectionName}]`));

  if (targetSection.length === 0) {
    throw new Error(`Cannot find [${sectionName}] section in config`);
  }

  const section = targetSection[0];

  for (const line of section.split("\n")) {
    const matched = line.startsWith(fieldName);
    if (matched) {
      const results = line.split("=");
      if (results.length === 2) {
        const key = results[1].trim();
        return key;
      }
    }
  }

  throw new Error(`Cannot find ${fieldName} in config`);
}

export default async function overrideEnv(env: Record<string, string>) {
  const configPath = env["VITE_BAZARR_CONFIG_FILE"];

  if (configPath === undefined) {
    return;
  }

  if (env["VITE_API_KEY"] === undefined) {
    try {
      const apiKey = await read(configPath, "auth", "apikey");

      env["VITE_API_KEY"] = apiKey;
      process.env["VITE_API_KEY"] = apiKey;
    } catch (err) {
      throw new Error(
        `No API key found, please run the backend first, (error: ${err.message})`
      );
    }
  }

  if (env["VITE_PROXY_URL"] === undefined) {
    try {
      const port = await read(configPath, "general", "port");
      const baseUrl = await read(configPath, "general", "base_url");

      const url = `http://localhost:${port}${baseUrl}`;

      env["VITE_PROXY_URL"] = url;
      process.env["VITE_PROXY_URL"] = url;
    } catch (err) {
      throw new Error(
        `No proxy url found, please run the backend first, (error: ${err.message})`
      );
    }
  }
}
